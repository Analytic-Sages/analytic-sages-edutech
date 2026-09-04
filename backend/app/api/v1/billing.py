from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_payment_service, get_settings, require_admin
from app.core.billing import BillingStatus
from app.core.config import Settings
from app.db.session import get_db
from app.models.billing import BillingAuditEvent
from app.models.payment import Payment
from app.models.user import User
from app.schemas.billing import (
    AdminBillingAccountPatch,
    AdminExtendRequest,
    AdminManualPaymentRequest,
    AdminWaiveRequest,
    BillingAccountPublic,
    CreateBillingAccountRequest,
    PayObligationRequest,
    TuitionPlanCreate,
    TuitionPlanPublic,
    TuitionPlanUpdate,
)
from app.schemas.payments import CheckoutResponse
from app.services.billing_accounts import BillingAccountService
from app.services.billing_obligations import PaymentObligationService
from app.services.billing_reconciliation import BillingReconciliationService
from app.services.payments import PaymentService
from app.services.tuition_plans import TuitionPlanService, money

router = APIRouter(tags=["billing"])
admin_router = APIRouter(prefix="/admin", tags=["admin-billing"])


def _plans(db: Session = Depends(get_db)) -> TuitionPlanService:
    return TuitionPlanService(db)


def _accounts(db: Session = Depends(get_db)) -> BillingAccountService:
    return BillingAccountService(db)


def _obligations(db: Session = Depends(get_db)) -> PaymentObligationService:
    return PaymentObligationService(db)


@router.get("/billing/plans", response_model=list[TuitionPlanPublic])
def list_billing_plans(
    cohort_id: UUID = Query(...),
    settings: Settings = Depends(get_settings),
    plans: TuitionPlanService = Depends(_plans),
) -> list[TuitionPlanPublic]:
    if not settings.billing_plans_enabled:
        return []
    return [
        TuitionPlanPublic.model_validate(p) for p in plans.list_plans_for_cohort(cohort_id=cohort_id)
    ]


@router.post("/billing/accounts", response_model=BillingAccountPublic)
def create_billing_account(
    payload: CreateBillingAccountRequest,
    current_user: CurrentUser,
    settings: Settings = Depends(get_settings),
    accounts: BillingAccountService = Depends(_accounts),
) -> BillingAccountPublic:
    if not settings.billing_plans_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tuition billing plans are not enabled",
        )
    account = accounts.create_account(
        student=current_user,
        tuition_plan_id=payload.tuition_plan_id,
        cohort_id=payload.cohort_id,
        course_id=payload.course_id,
        actor=current_user,
    )
    return BillingAccountPublic.model_validate(account)


@router.get("/billing/me", response_model=list[BillingAccountPublic])
def my_billing_accounts(
    current_user: CurrentUser,
    accounts: BillingAccountService = Depends(_accounts),
) -> list[BillingAccountPublic]:
    return [
        BillingAccountPublic.model_validate(a) for a in accounts.list_for_student(current_user.id)
    ]


@router.get("/billing/me/accounts/{account_id}", response_model=BillingAccountPublic)
def my_billing_account(
    account_id: UUID,
    current_user: CurrentUser,
    accounts: BillingAccountService = Depends(_accounts),
    db: Session = Depends(get_db),
) -> BillingAccountPublic:
    account = accounts.get_account(account_id, student_id=current_user.id)
    return BillingAccountPublic.model_validate(account)


@router.post(
    "/billing/me/obligations/{obligation_id}/pay",
    response_model=CheckoutResponse,
)
def pay_obligation(
    obligation_id: UUID,
    payload: PayObligationRequest,
    current_user: CurrentUser,
    settings: Settings = Depends(get_settings),
    obligations: PaymentObligationService = Depends(_obligations),
    payment_service: PaymentService = Depends(get_payment_service),
) -> CheckoutResponse:
    if not settings.billing_plans_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tuition billing plans are not enabled",
        )
    obligation = obligations.get_payable_obligation(obligation_id, student_id=current_user.id)
    return payment_service.create_obligation_checkout(
        user=current_user,
        obligation=obligation,
        provider_name=payload.provider,
    )


@admin_router.get("/billing/accounts", response_model=list[BillingAccountPublic])
def admin_list_billing_accounts(
    _: User = Depends(require_admin),
    accounts: BillingAccountService = Depends(_accounts),
    status_filter: BillingStatus | None = Query(default=None, alias="status"),
    cohort_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[BillingAccountPublic]:
    rows = accounts.list_admin(
        status_filter=status_filter, cohort_id=cohort_id, limit=limit
    )
    return [BillingAccountPublic.model_validate(a) for a in rows]


@admin_router.get("/billing/accounts/{account_id}", response_model=BillingAccountPublic)
def admin_get_billing_account(
    account_id: UUID,
    _: User = Depends(require_admin),
    accounts: BillingAccountService = Depends(_accounts),
) -> BillingAccountPublic:
    return BillingAccountPublic.model_validate(accounts.get_account(account_id))


@admin_router.patch("/billing/accounts/{account_id}", response_model=BillingAccountPublic)
def admin_patch_billing_account(
    account_id: UUID,
    payload: AdminBillingAccountPatch,
    admin: User = Depends(require_admin),
    accounts: BillingAccountService = Depends(_accounts),
) -> BillingAccountPublic:
    account = accounts.update_status(
        account_id=account_id,
        billing_status=payload.billing_status,
        actor=admin,
        note=payload.note,
    )
    return BillingAccountPublic.model_validate(account)


@admin_router.post(
    "/billing/obligations/{obligation_id}/waive",
    response_model=BillingAccountPublic,
)
def admin_waive_obligation(
    obligation_id: UUID,
    payload: AdminWaiveRequest,
    admin: User = Depends(require_admin),
    obligations: PaymentObligationService = Depends(_obligations),
    accounts: BillingAccountService = Depends(_accounts),
) -> BillingAccountPublic:
    obligation = obligations.waive(
        obligation_id=obligation_id, actor=admin, note=payload.note
    )
    return BillingAccountPublic.model_validate(
        accounts.get_account(obligation.billing_account_id)
    )


@admin_router.post(
    "/billing/obligations/{obligation_id}/extend",
    response_model=BillingAccountPublic,
)
def admin_extend_obligation(
    obligation_id: UUID,
    payload: AdminExtendRequest,
    admin: User = Depends(require_admin),
    obligations: PaymentObligationService = Depends(_obligations),
    accounts: BillingAccountService = Depends(_accounts),
) -> BillingAccountPublic:
    obligation = obligations.extend_due_date(
        obligation_id=obligation_id,
        due_date=payload.due_date,
        actor=admin,
        note=payload.note,
    )
    return BillingAccountPublic.model_validate(
        accounts.get_account(obligation.billing_account_id)
    )


@admin_router.post(
    "/billing/accounts/{account_id}/manual-payment",
    response_model=BillingAccountPublic,
)
def admin_manual_payment(
    account_id: UUID,
    payload: AdminManualPaymentRequest,
    admin: User = Depends(require_admin),
    accounts: BillingAccountService = Depends(_accounts),
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
) -> BillingAccountPublic:
    from datetime import UTC

    from app.core.payments import PaymentProviderName, PaymentStatus
    from app.models.billing import PaymentObligation
    from app.core.billing import ObligationStatus

    account = accounts.get_account(account_id)
    open_obs = sorted(
        [
            o
            for o in account.obligations
            if o.status
            in {ObligationStatus.OPEN, ObligationStatus.PAST_DUE, ObligationStatus.PROCESSING}
        ],
        key=lambda o: o.sequence_number,
    )
    if not open_obs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No open obligation to apply payment"
        )
    obligation = open_obs[0]
    amount = money(payload.amount)
    if amount != money(obligation.amount_due):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual payment amount must match the open obligation",
        )

    payment = Payment(
        order_id=f"manual-{account.id.hex[:12]}-{obligation.sequence_number}",
        user_id=account.student_id,
        course_id=account.course_id,
        cohort_id=account.cohort_id,
        billing_account_id=account.id,
        payment_obligation_id=obligation.id,
        provider=PaymentProviderName.MOCK,
        provider_payment_id=f"manual_{obligation.id}",
        amount=int(amount),
        currency=account.currency,
        status=PaymentStatus.CONFIRMED,
        confirmed_at=datetime.now(UTC),
        metadata_json={"manual": True, "note": payload.note, "actor_id": str(admin.id)},
    )
    db.add(payment)
    db.flush()
    BillingReconciliationService(db).reconcile_confirmed_payment(payment)
    if payload.unlock_access and account.cohort_id:
        payment_service._unlock_cohort_membership(payment)  # noqa: SLF001

    from app.core.config import get_settings
    from app.services.referrals import ReferralCommissionService

    ReferralCommissionService(db, get_settings()).handle_successful_payment(payment)

    db.add(
        BillingAuditEvent(
            actor_id=admin.id,
            action="billing_account.manual_payment",
            entity_type="student_billing_account",
            entity_id=account.id,
            note=payload.note,
            after_json={"obligation_id": str(obligation.id), "amount": str(amount)},
        )
    )
    db.commit()
    return BillingAccountPublic.model_validate(accounts.get_account(account_id))


@admin_router.get("/billing/export.csv")
def admin_billing_export(
    _: User = Depends(require_admin),
    accounts: BillingAccountService = Depends(_accounts),
) -> Response:
    rows = accounts.list_admin(limit=500)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "account_id",
            "student_id",
            "cohort_id",
            "status",
            "currency",
            "final_amount_due",
            "amount_paid",
            "amount_outstanding",
            "created_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                str(row.id),
                str(row.student_id),
                str(row.cohort_id) if row.cohort_id else "",
                row.billing_status.value,
                row.currency,
                str(row.final_amount_due),
                str(row.amount_paid),
                str(row.amount_outstanding),
                row.created_at.isoformat(),
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=billing-accounts.csv"},
    )


@admin_router.get("/tuition-plans", response_model=list[TuitionPlanPublic])
def admin_list_tuition_plans(
    _: User = Depends(require_admin),
    cohort_id: UUID | None = None,
    plans: TuitionPlanService = Depends(_plans),
    db: Session = Depends(get_db),
) -> list[TuitionPlanPublic]:
    if cohort_id:
        rows = plans.list_plans_for_cohort(cohort_id=cohort_id, active_only=False)
    else:
        from app.models.billing import TuitionPlan
        from sqlalchemy.orm import selectinload

        rows = list(
            db.scalars(
                select(TuitionPlan)
                .options(selectinload(TuitionPlan.schedules))
                .order_by(TuitionPlan.sort_order, TuitionPlan.created_at)
            ).all()
        )
    return [TuitionPlanPublic.model_validate(p) for p in rows]


@admin_router.post("/tuition-plans", response_model=TuitionPlanPublic)
def admin_create_tuition_plan(
    payload: TuitionPlanCreate,
    admin: User = Depends(require_admin),
    plans: TuitionPlanService = Depends(_plans),
) -> TuitionPlanPublic:
    plan = plans.create_plan(payload, actor=admin)
    return TuitionPlanPublic.model_validate(plan)


@admin_router.patch("/tuition-plans/{plan_id}", response_model=TuitionPlanPublic)
def admin_update_tuition_plan(
    plan_id: UUID,
    payload: TuitionPlanUpdate,
    admin: User = Depends(require_admin),
    plans: TuitionPlanService = Depends(_plans),
) -> TuitionPlanPublic:
    plan = plans.update_plan(plan_id, payload, actor=admin)
    return TuitionPlanPublic.model_validate(plan)
