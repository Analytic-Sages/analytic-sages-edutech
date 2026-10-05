from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    get_live_learning_service,
    get_report_service,
    require_admin,
    require_instructor,
)
from app.models.user import User
from app.schemas.reports import CohortReport
from app.schemas.live import (
    AttendanceBulkWrite,
    AttendanceRecordPublic,
    CohortAdminUpsert,
    CohortStudentDetailPublic,
    InstructorStudentRow,
    MyLiveEnrollmentPublic,
    ProgrammeDetailPublic,
    ProgrammePublic,
    ProgrammeUpsert,
)
from app.services.live import LiveLearningService
from app.services.reports import CohortReportService

router = APIRouter(tags=["live"])


@router.get("/programmes", response_model=list[ProgrammePublic])
def list_programmes(live: LiveLearningService = Depends(get_live_learning_service)) -> list[ProgrammePublic]:
    return live.list_programmes()


@router.get("/programmes/{slug}", response_model=ProgrammeDetailPublic)
def get_programme(
    slug: str,
    live: LiveLearningService = Depends(get_live_learning_service),
) -> ProgrammeDetailPublic:
    return live.get_programme(slug)


@router.get("/me/live", response_model=list[MyLiveEnrollmentPublic])
def my_live_enrollments(
    current_user: CurrentUser,
    live: LiveLearningService = Depends(get_live_learning_service),
) -> list[MyLiveEnrollmentPublic]:
    return live.my_live_enrollments(current_user)


@router.get("/cohorts/{cohort_id}", response_model=CohortStudentDetailPublic)
def get_my_cohort(
    cohort_id: UUID,
    current_user: CurrentUser,
    live: LiveLearningService = Depends(get_live_learning_service),
) -> CohortStudentDetailPublic:
    return live.get_cohort_for_student(current_user, cohort_id)


@router.get("/cohorts/{cohort_id}/attendance", response_model=list[AttendanceRecordPublic])
def my_attendance(
    cohort_id: UUID,
    current_user: CurrentUser,
    live: LiveLearningService = Depends(get_live_learning_service),
) -> list[AttendanceRecordPublic]:
    return live.my_attendance(current_user, cohort_id)


@router.get("/instructor/cohorts", response_model=list[CohortStudentDetailPublic])
def instructor_cohorts(
    current_user: User = Depends(require_instructor),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> list[CohortStudentDetailPublic]:
    return live.list_instructor_cohorts(current_user)


@router.get("/instructor/cohorts/{cohort_id}/students", response_model=list[InstructorStudentRow])
def instructor_students(
    cohort_id: UUID,
    current_user: User = Depends(require_instructor),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> list[InstructorStudentRow]:
    return live.list_cohort_students(current_user, cohort_id)


@router.get("/instructor/cohorts/{cohort_id}/attendance", response_model=list[AttendanceRecordPublic])
def instructor_attendance(
    cohort_id: UUID,
    current_user: User = Depends(require_instructor),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> list[AttendanceRecordPublic]:
    return live.get_cohort_attendance(current_user, cohort_id)


@router.put("/instructor/cohorts/{cohort_id}/attendance", response_model=list[AttendanceRecordPublic])
def record_attendance(
    cohort_id: UUID,
    payload: AttendanceBulkWrite,
    current_user: User = Depends(require_instructor),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> list[AttendanceRecordPublic]:
    return live.record_attendance(current_user, cohort_id, payload)


@router.get("/instructor/cohorts/{cohort_id}/report", response_model=CohortReport)
def cohort_report(
    cohort_id: UUID,
    current_user: User = Depends(require_instructor),
    reports: CohortReportService = Depends(get_report_service),
) -> CohortReport:
    return reports.cohort_report(current_user, cohort_id)


@router.post("/admin/programmes", response_model=ProgrammePublic, status_code=201)
def create_programme(
    payload: ProgrammeUpsert,
    _: User = Depends(require_admin),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> ProgrammePublic:
    return live.create_programme(payload)


@router.patch("/admin/programmes/{programme_id}", response_model=ProgrammePublic)
def update_programme(
    programme_id: UUID,
    payload: ProgrammeUpsert,
    _: User = Depends(require_admin),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> ProgrammePublic:
    return live.update_programme(programme_id, payload)


@router.post("/admin/cohorts", response_model=CohortStudentDetailPublic, status_code=201)
def create_cohort(
    payload: CohortAdminUpsert,
    _: User = Depends(require_admin),
    live: LiveLearningService = Depends(get_live_learning_service),
) -> CohortStudentDetailPublic:
    return live.create_cohort(payload)
