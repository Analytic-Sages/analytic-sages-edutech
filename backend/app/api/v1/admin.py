from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.deps import (
    get_admin_service,
    get_admin_students_service,
    get_auth_service,
    get_billing_reminder_service,
    get_classroom_admin_service,
    get_cloudflare_stream_service,
    get_course_admin_service,
    get_payment_service,
    get_quiz_admin_service,
    get_self_paced_service,
    get_storage_service,
    require_admin,
    require_catalog_ops,
    require_course_author,
)
from app.models.user import User
from app.schemas.admin import (
    AdminAnalytics,
    AdminCohortDetail,
    AdminOverview,
    AdminPaymentRow,
    AdminUserRow,
    InviteInstructorRequest,
    InviteInstructorResponse,
    ReconcilePaymentRequest,
)
from app.schemas.admin_students import (
    AdminInstallmentRow,
    AdminStudentList,
    InstallmentReminderRequest,
    ReminderResult,
)
from app.schemas.classroom_admin import (
    AdminCohortOption,
    AdminLiveSessionCreate,
    AdminLiveSessionRow,
    AdminLiveSessionUpdate,
)
from app.schemas.lms_admin import (
    AdminCourseDetail,
    AdminCourseUpdate,
    AdminCourseUpsert,
    AdminLessonResourceUpsert,
    AdminLessonRow,
    AdminLessonUpdate,
    AdminLessonUpsert,
    AdminModuleRow,
    AdminModuleUpdate,
    AdminModuleUpsert,
    AdminVideoInfo,
    AdminVideoUploadResponse,
)
from app.schemas.self_paced import AdminCourseAnalytics, AdminCourseRow
from app.schemas.quizzes import (
    AdminQuizDetail,
    AdminQuizRow,
    QuizCreate,
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizUpdate,
)
from app.services.admin import AdminService
from app.services.admin_students import AdminStudentsService
from app.services.auth import AuthService
from app.services.billing_reminders import BillingReminderService
from app.services.classroom_admin import ClassroomAdminService
from app.services.cloudflare_stream import CloudflareStreamError, CloudflareStreamService
from app.services.course_admin import CourseAdminService
from app.services.payments import PaymentService
from app.services.quiz_admin import QuizAdminService
from app.services.self_paced import SelfPacedService
from app.services.storage import StorageService

router = APIRouter(prefix="/admin", tags=["admin"])


def _invite_response(result) -> InviteInstructorResponse:
    user = result.user
    role_labels = {
        "operations": "operations",
        "partnerships": "grants & partnerships",
        "editor": "editor",
        "author": "author",
        "instructor": "instructor",
    }
    role_label = role_labels.get(user.role.value, "staff")
    if result.promoted and not result.resent:
        if user.password_hash:
            message = (
                f"Promoted {user.email} to {role_label}. "
                "They can sign in with their existing password."
            )
        else:
            message = (
                f"Promoted {user.email} to {role_label} and sent an invite to set a password."
            )
    elif result.resent:
        message = f"Invite resent to {user.email}."
    else:
        message = f"Invite sent to {user.email}. They have 7 days to set a password."
    return InviteInstructorResponse(
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        resent=result.resent,
        promoted=result.promoted,
        message=message,
    )


@router.get("/overview", response_model=AdminOverview)
def admin_overview(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
) -> AdminOverview:
    return admin.overview()


@router.get("/analytics", response_model=AdminAnalytics)
def admin_analytics(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
) -> AdminAnalytics:
    return admin.analytics()


@router.get("/users", response_model=list[AdminUserRow])
def admin_users(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[AdminUserRow]:
    return admin.list_users(limit=limit)


@router.post("/users/{user_id}/remove-staff-access", response_model=AdminUserRow)
def remove_staff_access(
    user_id: UUID,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
    admin: AdminService = Depends(get_admin_service),
) -> AdminUserRow:
    user = auth.remove_staff_access(user_id)
    featured = admin._featured_cohort()
    member_ids = admin._member_user_ids(featured.id) if featured else set()
    return admin._user_rows([user], member_ids)[0]


@router.get("/payments", response_model=list[AdminPaymentRow])
def admin_payments(
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[AdminPaymentRow]:
    return admin.list_payments(limit=limit)


@router.post("/payments/{order_id}/reconcile", response_model=AdminPaymentRow)
def admin_reconcile_payment(
    order_id: str,
    payload: ReconcilePaymentRequest,
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
    payment_service: PaymentService = Depends(get_payment_service),
) -> AdminPaymentRow:
    payment = payment_service.reconcile_payment(order_id=order_id, payment_id=payload.payment_id)
    return admin.payment_row(payment)


@router.post("/payments/reconcile-stale")
def admin_reconcile_stale_payments(
    _: User = Depends(require_admin),
    payment_service: PaymentService = Depends(get_payment_service),
    older_than_seconds: int = Query(default=120, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, int]:
    """Clear the backlog in one click: pull the real status for every stale
    pending NOWPayments order (missed/late IPNs) and unlock any that finished."""
    return payment_service.reconcile_stale_nowpayments(
        older_than_seconds=older_than_seconds, limit=limit
    )


@router.get("/courses", response_model=list[AdminCourseRow])
def admin_courses(
    _: User = Depends(require_catalog_ops),
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> list[AdminCourseRow]:
    return lms.list_admin_courses()


@router.get("/courses/{slug}/analytics", response_model=AdminCourseAnalytics)
def admin_course_analytics(
    slug: str,
    _: User = Depends(require_admin),
    lms: SelfPacedService = Depends(get_self_paced_service),
) -> AdminCourseAnalytics:
    return lms.course_analytics(slug)


@router.get("/cohorts/{slug}", response_model=AdminCohortDetail)
def admin_cohort(
    slug: str,
    _: User = Depends(require_admin),
    admin: AdminService = Depends(get_admin_service),
) -> AdminCohortDetail:
    return admin.cohort_detail(slug)


@router.get("/classroom/cohorts", response_model=list[AdminCohortOption])
def admin_classroom_cohorts(
    _: User = Depends(require_admin),
    classroom: ClassroomAdminService = Depends(get_classroom_admin_service),
) -> list[AdminCohortOption]:
    return classroom.list_cohorts()


@router.get("/classroom/sessions", response_model=list[AdminLiveSessionRow])
def admin_classroom_sessions(
    _: User = Depends(require_admin),
    classroom: ClassroomAdminService = Depends(get_classroom_admin_service),
    cohort_id: UUID | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
) -> list[AdminLiveSessionRow]:
    return classroom.list_sessions(cohort_id=cohort_id, limit=limit)


@router.post("/classroom/sessions", response_model=AdminLiveSessionRow, status_code=201)
def admin_create_classroom_session(
    payload: AdminLiveSessionCreate,
    _: User = Depends(require_admin),
    classroom: ClassroomAdminService = Depends(get_classroom_admin_service),
) -> AdminLiveSessionRow:
    return classroom.create_session(payload)


@router.patch("/classroom/sessions/{session_id}", response_model=AdminLiveSessionRow)
def admin_update_classroom_session(
    session_id: UUID,
    payload: AdminLiveSessionUpdate,
    _: User = Depends(require_admin),
    classroom: ClassroomAdminService = Depends(get_classroom_admin_service),
) -> AdminLiveSessionRow:
    return classroom.update_session(session_id, payload)


@router.post("/classroom/sessions/{session_id}/cancel", response_model=AdminLiveSessionRow)
def admin_cancel_classroom_session(
    session_id: UUID,
    _: User = Depends(require_admin),
    classroom: ClassroomAdminService = Depends(get_classroom_admin_service),
) -> AdminLiveSessionRow:
    return classroom.cancel_session(session_id)


@router.delete("/classroom/sessions/{session_id}", status_code=204)
def admin_delete_classroom_session(
    session_id: UUID,
    _: User = Depends(require_admin),
    classroom: ClassroomAdminService = Depends(get_classroom_admin_service),
) -> None:
    classroom.delete_session(session_id)


@router.get("/students", response_model=AdminStudentList)
def admin_students(
    _: User = Depends(require_admin),
    students: AdminStudentsService = Depends(get_admin_students_service),
    payment_status: str = Query(default="all", pattern="^(all|paid|partial|unpaid)$"),
    plan: str = Query(default="all", pattern="^(all|full|installments)$"),
    cohort_id: UUID | None = None,
    has_outstanding: bool | None = None,
    q: str | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
) -> AdminStudentList:
    """Students with a paid / partial / unpaid payment status and next-due info."""
    return students.list_students(
        payment_status=payment_status,
        plan=plan,
        cohort_id=cohort_id,
        has_outstanding=has_outstanding,
        q=q,
        limit=limit,
    )


@router.get("/installments", response_model=list[AdminInstallmentRow])
def admin_installments(
    _: User = Depends(require_admin),
    students: AdminStudentsService = Depends(get_admin_students_service),
    status_filter: str = Query(
        default="all",
        alias="status",
        pattern="^(all|overdue|due_soon|upcoming|paid)$",
    ),
    cohort_id: UUID | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
) -> list[AdminInstallmentRow]:
    """Installment board: overdue / due-soon / upcoming obligations with deadlines."""
    return students.list_installments(
        status_filter=status_filter, cohort_id=cohort_id, limit=limit
    )


@router.post("/obligations/{obligation_id}/remind", response_model=ReminderResult)
def admin_remind_obligation(
    obligation_id: UUID,
    _: User = Depends(require_admin),
    reminders: BillingReminderService = Depends(get_billing_reminder_service),
) -> ReminderResult:
    sent = reminders.remind_obligation(obligation_id)
    return ReminderResult(sent=1 if sent else 0, skipped=0 if sent else 1, failed=0)


@router.post("/installments/remind", response_model=ReminderResult)
def admin_remind_installments(
    payload: InstallmentReminderRequest,
    _: User = Depends(require_admin),
    reminders: BillingReminderService = Depends(get_billing_reminder_service),
) -> ReminderResult:
    """Bulk-send installment reminders (overdue / due-soon / all)."""
    outcome = reminders.run(scope=payload.scope, cohort_id=payload.cohort_id)
    return ReminderResult(**outcome.as_dict())


@router.post("/instructors", response_model=InviteInstructorResponse)
def invite_instructor(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
    admin: AdminService = Depends(get_admin_service),
) -> InviteInstructorResponse:
    result = auth.invite_instructor(email=payload.email, full_name=payload.full_name)
    admin.add_instructor_to_featured_cohort(result.user)
    return _invite_response(result)


@router.post("/operations", response_model=InviteInstructorResponse)
def invite_operations(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    return _invite_response(auth.invite_operations(email=payload.email, full_name=payload.full_name))


@router.post("/partnerships", response_model=InviteInstructorResponse)
def invite_partnerships(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    return _invite_response(auth.invite_partnerships(email=payload.email, full_name=payload.full_name))


@router.post("/editors", response_model=InviteInstructorResponse)
def invite_editor(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    return _invite_response(auth.invite_editor(email=payload.email, full_name=payload.full_name))


@router.post("/authors", response_model=InviteInstructorResponse)
def invite_author(
    payload: InviteInstructorRequest,
    _: User = Depends(require_admin),
    auth: AuthService = Depends(get_auth_service),
) -> InviteInstructorResponse:
    return _invite_response(auth.invite_author(email=payload.email, full_name=payload.full_name))
# ---------- Course authoring (no developer needed) ----------


@router.get("/courses/{slug}/detail", response_model=AdminCourseDetail)
def admin_course_detail(
    slug: str,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminCourseDetail:
    return courses.get_course(slug)


@router.post("/courses", response_model=AdminCourseDetail, status_code=201)
def admin_create_course(
    payload: AdminCourseUpsert,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminCourseDetail:
    return courses.create_course(payload)


@router.patch("/courses/{slug}", response_model=AdminCourseDetail)
def admin_update_course(
    slug: str,
    payload: AdminCourseUpdate,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminCourseDetail:
    return courses.update_course(slug, payload)


@router.delete("/courses/{slug}", status_code=204)
def admin_delete_course(
    slug: str,
    _: User = Depends(require_admin),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> None:
    courses.delete_course(slug)


@router.post("/courses/{slug}/modules", response_model=AdminModuleRow, status_code=201)
def admin_create_module(
    slug: str,
    payload: AdminModuleUpsert,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminModuleRow:
    return courses.create_module(slug, payload)


@router.patch("/modules/{module_id}", response_model=AdminModuleRow)
def admin_update_module(
    module_id: UUID,
    payload: AdminModuleUpdate,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminModuleRow:
    return courses.update_module(module_id, payload)


@router.delete("/modules/{module_id}", status_code=204)
def admin_delete_module(
    module_id: UUID,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> None:
    courses.delete_module(module_id)
@router.post("/modules/{module_id}/lessons", response_model=AdminLessonRow, status_code=201)
def admin_create_lesson(
    module_id: UUID,
    payload: AdminLessonUpsert,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminLessonRow:
    return courses.create_lesson(module_id, payload)


@router.patch("/lessons/{lesson_id}", response_model=AdminLessonRow)
def admin_update_lesson(
    lesson_id: UUID,
    payload: AdminLessonUpdate,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminLessonRow:
    return courses.update_lesson(lesson_id, payload)


@router.delete("/lessons/{lesson_id}", status_code=204)
def admin_delete_lesson(
    lesson_id: UUID,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> None:
    courses.delete_lesson(lesson_id)


@router.post("/lessons/{lesson_id}/resources", response_model=AdminLessonRow)
def admin_add_lesson_resource(
    lesson_id: UUID,
    payload: AdminLessonResourceUpsert,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminLessonRow:
    return courses.add_lesson_resource(lesson_id, payload)


@router.delete("/lessons/{lesson_id}/resources", response_model=AdminLessonRow)
def admin_remove_lesson_resource(
    lesson_id: UUID,
    url: str = Query(...),
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
) -> AdminLessonRow:
    return courses.remove_lesson_resource(lesson_id, url)


@router.post("/lessons/{lesson_id}/resources/upload", response_model=AdminLessonRow)
async def admin_upload_lesson_resource(
    lesson_id: UUID,
    label: str = Query(..., min_length=1, max_length=200),
    kind: str = Query(default="other", pattern="^(pdf|slides|dataset|code|repo|reading|doc|other)$"),
    file: UploadFile = File(...),
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
    storage: StorageService = Depends(get_storage_service),
) -> AdminLessonRow:
    """Upload a downloadable resource (PDF, slides, dataset, source, zip) for a lesson."""
    url = await storage.save_document(file)
    return courses.add_lesson_resource(
        lesson_id, AdminLessonResourceUpsert(label=label, url=url, kind=kind)
    )
# ---------- Cloudflare Stream video uploads ----------


@router.post("/lessons/{lesson_id}/video/direct-upload", response_model=AdminVideoUploadResponse)
def admin_lesson_video_upload(
    lesson_id: UUID,
    _: User = Depends(require_course_author),
    courses: CourseAdminService = Depends(get_course_admin_service),
    stream: CloudflareStreamService = Depends(get_cloudflare_stream_service),
    max_duration_seconds: int | None = Query(default=None, ge=30, le=21600),
) -> AdminVideoUploadResponse:
    """Create a Cloudflare Stream upload URL and point the lesson at the new UID.

    The browser POSTs the video file to ``upload_url``; Cloudflare then transcodes
    and the Stream player plays it back via the ``embed_url``.
    """
    courses.get_lesson(lesson_id)  # 404 if the lesson doesn't exist
    try:
        upload = stream.create_direct_upload(
            max_duration_seconds=max_duration_seconds,
            creator=f"analyticsages-lesson-{lesson_id}",
            meta={"lesson_id": str(lesson_id)},
        )
    except CloudflareStreamError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    courses.set_lesson_video(lesson_id, provider="cloudflare_stream", video_id=upload.uid)
    return AdminVideoUploadResponse(
        uid=upload.uid,
        upload_url=upload.upload_url,
        embed_url=stream.embed_url(upload.uid),
        hls_url=stream.hls_url(upload.uid),
        thumbnail_url=stream.thumbnail_url(upload.uid),
        mode=stream.mode,
    )


@router.get("/videos/{uid}", response_model=AdminVideoInfo)
def admin_video_info(
    uid: str,
    _: User = Depends(require_course_author),
    stream: CloudflareStreamService = Depends(get_cloudflare_stream_service),
) -> AdminVideoInfo:
    try:
        video = stream.get_video(uid)
    except CloudflareStreamError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return AdminVideoInfo(
        uid=video.uid,
        status=video.status,
        duration_seconds=video.duration_seconds,
        thumbnail_url=video.thumbnail_url,
        embed_url=video.embed_url,
        hls_url=video.hls_url,
        mode=stream.mode,
    )
# ---------- Quizzes ----------


@router.get("/quizzes", response_model=list[AdminQuizRow])
def admin_list_quizzes(
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
    course_slug: str | None = Query(default=None),
) -> list[AdminQuizRow]:
    return quizzes.list_quizzes(course_slug=course_slug)


@router.get("/quizzes/{quiz_id}", response_model=AdminQuizDetail)
def admin_get_quiz(
    quiz_id: UUID,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> AdminQuizDetail:
    return quizzes.get_quiz(quiz_id)


@router.post("/courses/{slug}/quizzes", response_model=AdminQuizDetail, status_code=201)
def admin_create_quiz(
    slug: str,
    payload: QuizCreate,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> AdminQuizDetail:
    return quizzes.create_quiz(slug, payload)


@router.patch("/quizzes/{quiz_id}", response_model=AdminQuizDetail)
def admin_update_quiz(
    quiz_id: UUID,
    payload: QuizUpdate,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> AdminQuizDetail:
    return quizzes.update_quiz(quiz_id, payload)


@router.delete("/quizzes/{quiz_id}", status_code=204)
def admin_delete_quiz(
    quiz_id: UUID,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> None:
    quizzes.delete_quiz(quiz_id)


@router.post("/quizzes/{quiz_id}/questions", response_model=AdminQuizDetail, status_code=201)
def admin_add_quiz_question(
    quiz_id: UUID,
    payload: QuizQuestionCreate,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> AdminQuizDetail:
    return quizzes.add_question(quiz_id, payload)


@router.patch("/quiz-questions/{question_id}", response_model=AdminQuizDetail)
def admin_update_quiz_question(
    question_id: UUID,
    payload: QuizQuestionUpdate,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> AdminQuizDetail:
    return quizzes.update_question(question_id, payload)


@router.delete("/quiz-questions/{question_id}", response_model=AdminQuizDetail)
def admin_delete_quiz_question(
    question_id: UUID,
    _: User = Depends(require_course_author),
    quizzes: QuizAdminService = Depends(get_quiz_admin_service),
) -> AdminQuizDetail:
    return quizzes.delete_question(question_id)
