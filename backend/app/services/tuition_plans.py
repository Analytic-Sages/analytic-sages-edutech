from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.billing import DueRule, TuitionPlanType
from app.models.billing import TuitionPlan, TuitionPlanSchedule
from app.models.classroom import Cohort
from app.models.user import User
from app.schemas.billing import (
    TuitionPlanCreate,
    TuitionPlanScheduleCreate,
    TuitionPlanUpdate,
)


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def to_major_int(amount: Decimal) -> int:
    """Provider checkout uses integer major units (e.g. 200 = $200)."""
    quantized = money(amount)
    if quantized != quantized.to_integral_value():
        # Providers charge whole major units today; reject fractional for attempts.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installment amounts must be whole currency units for checkout",
        )
    return int(quantized)


class TuitionPlanService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_plans_for_cohort(
        self, *, cohort_id: UUID, active_only: bool = True
    ) -> list[TuitionPlan]:
        now = datetime.now(UTC)
        stmt = (
            select(TuitionPlan)
            .options(selectinload(TuitionPlan.schedules))
            .where(TuitionPlan.cohort_id == cohort_id)
            .order_by(TuitionPlan.sort_order, TuitionPlan.created_at)
        )
        if active_only:
            stmt = stmt.where(TuitionPlan.active.is_(True))
        plans = list(self.db.scalars(stmt).all())
        if not active_only:
            return plans
        return [
            plan
            for plan in plans
            if (plan.available_from is None or plan.available_from <= now)
            and (plan.available_until is None or plan.available_until >= now)
        ]

    def get_plan(self, plan_id: UUID, *, with_schedules: bool = True) -> TuitionPlan:
        stmt = select(TuitionPlan).where(TuitionPlan.id == plan_id)
        if with_schedules:
            stmt = stmt.options(selectinload(TuitionPlan.schedules))
        plan = self.db.scalar(stmt)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tuition plan not found")
        return plan

    def create_plan(self, payload: TuitionPlanCreate, *, actor: User | None = None) -> TuitionPlan:
        self._validate_schedules(payload.schedules, payload.plan_type, payload.base_amount)
        if payload.cohort_id:
            cohort = self.db.get(Cohort, payload.cohort_id)
            if not cohort:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")

        plan = TuitionPlan(
            course_id=payload.course_id,
            cohort_id=payload.cohort_id,
            name=payload.name,
            description=payload.description,
            plan_type=payload.plan_type,
            base_currency=payload.base_currency.upper(),
            base_amount=money(payload.base_amount),
            number_of_installments=len(payload.schedules),
            active=payload.active,
            available_from=payload.available_from,
            available_until=payload.available_until,
            sort_order=payload.sort_order,
        )
        self.db.add(plan)
        self.db.flush()
        for row in payload.schedules:
            self.db.add(
                TuitionPlanSchedule(
                    tuition_plan_id=plan.id,
                    sequence_number=row.sequence_number,
                    label=row.label,
                    amount=money(row.amount),
                    due_rule=row.due_rule,
                    due_date=row.due_date,
                    week_number=row.week_number,
                    offset_days=row.offset_days,
                )
            )
        self.db.commit()
        return self.get_plan(plan.id)

    def update_plan(
        self, plan_id: UUID, payload: TuitionPlanUpdate, *, actor: User | None = None
    ) -> TuitionPlan:
        plan = self.get_plan(plan_id)
        data = payload.model_dump(exclude_unset=True)
        schedules = data.pop("schedules", None)
        for key, value in data.items():
            if key == "base_amount" and value is not None:
                setattr(plan, key, money(value))
            elif key == "base_currency" and value is not None:
                setattr(plan, key, str(value).upper())
            else:
                setattr(plan, key, value)

        if schedules is not None:
            schedule_models = [TuitionPlanScheduleCreate.model_validate(s) for s in schedules]
            base = money(plan.base_amount)
            self._validate_schedules(schedule_models, plan.plan_type, base)
            plan.schedules.clear()
            self.db.flush()
            for row in schedule_models:
                plan.schedules.append(
                    TuitionPlanSchedule(
                        tuition_plan_id=plan.id,
                        sequence_number=row.sequence_number,
                        label=row.label,
                        amount=money(row.amount),
                        due_rule=row.due_rule,
                        due_date=row.due_date,
                        week_number=row.week_number,
                        offset_days=row.offset_days,
                    )
                )
            plan.number_of_installments = len(schedule_models)

        self.db.commit()
        return self.get_plan(plan.id)

    def _validate_schedules(
        self,
        schedules: list[TuitionPlanScheduleCreate],
        plan_type: TuitionPlanType,
        base_amount: Decimal,
    ) -> None:
        if not schedules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tuition plan requires at least one schedule row",
            )
        seqs = [s.sequence_number for s in schedules]
        if sorted(seqs) != list(range(1, len(schedules) + 1)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule sequence_number must be contiguous starting at 1",
            )
        total = sum((money(s.amount) for s in schedules), Decimal("0.00"))
        if total != money(base_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule amounts must sum to base_amount",
            )
        if plan_type == TuitionPlanType.ONE_TIME and len(schedules) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="one_time plans require exactly one schedule row",
            )
        for row in schedules:
            if row.due_rule == DueRule.SPECIFIC_DATE and row.due_date is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="specific_date schedules require due_date",
                )
            if row.due_rule == DueRule.WEEK_NUMBER and row.week_number is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="week_number schedules require week_number",
                )
