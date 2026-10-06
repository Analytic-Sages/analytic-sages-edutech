from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.live import AttendanceStatus, ProgrammeStatus
from app.core.roles import UserRole
from app.models.attendance import Attendance
from app.models.classroom import (
    Cohort,
    CohortMember,
    CohortMemberRole,
    CohortStatus,
    LiveSession,
    LiveSessionStatus,
)
from app.models.programme import Programme
from app.models.user import User
from app.schemas.live import (
    AttendanceBulkWrite,
    AttendanceRecordPublic,
    AttendanceSummaryPublic,
    CohortAdminUpsert,
    CohortStudentDetailPublic,
    InstructorStudentRow,
    MyLiveEnrollmentPublic,
    ProgrammeCohortPublic,
    ProgrammeDetailPublic,
    ProgrammePublic,
    ProgrammeUpsert,
)
from app.services.classroom import ClassroomService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LiveLearningService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.classroom = ClassroomService(db, settings)

    def _get_programme(self, slug: str) -> Programme:
        programme = self.db.scalar(select(Programme).where(Programme.slug == slug))
        if not programme:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme not found")
        return programme

    def _get_cohort(self, cohort_id: UUID) -> Cohort:
        cohort = self.db.get(Cohort, cohort_id)
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
        return cohort

    def _sessions(self, cohort_id: UUID) -> list[LiveSession]:
        return list(
            self.db.scalars(
                select(LiveSession)
                .where(
                    LiveSession.cohort_id == cohort_id,
                    LiveSession.status != LiveSessionStatus.CANCELLED,
                )
                .order_by(LiveSession.starts_at.asc())
            ).all()
        )

    def _attendance_summary(
        self, session_ids: list[UUID], user_id: UUID | None = None
    ) -> AttendanceSummaryPublic:
        if not session_ids:
            return AttendanceSummaryPublic()
        stmt = select(Attendance).where(Attendance.session_id.in_(session_ids))
        if user_id is not None:
            stmt = stmt.where(Attendance.user_id == user_id)
        rows = list(self.db.scalars(stmt).all())
        return AttendanceSummaryPublic(
            attended=sum(1 for r in rows if r.status == AttendanceStatus.ATTENDED),
            late=sum(1 for r in rows if r.status == AttendanceStatus.LATE),
            absent=sum(1 for r in rows if r.status == AttendanceStatus.ABSENT),
            total=len(rows),
        )

    def _progress_percent(self, user_id: UUID, cohort_id: UUID) -> int:
        sessions = self._sessions(cohort_id)
        if not sessions:
            return 0
        rows = list(
            self.db.scalars(
                select(Attendance).where(
                    Attendance.user_id == user_id,
                    Attendance.session_id.in_([s.id for s in sessions]),
                )
            ).all()
        )
        present = sum(
            1 for r in rows if r.status in {AttendanceStatus.ATTENDED, AttendanceStatus.LATE}
        )
        return round((present / len(sessions)) * 100)

    def _next_session(self, sessions: list[LiveSession]) -> LiveSession | None:
        for session in sessions:
            phase = self.classroom._effective_phase(session)
            if phase in {"live", "upcoming"}:
                return session
        return None

    def _cohort_enrollment(self, user: User, cohort_id: UUID) -> CohortMember | None:
        return self.db.scalar(
            select(CohortMember).where(
                CohortMember.cohort_id == cohort_id,
                CohortMember.user_id == user.id,
            )
        )

    def _require_student_enrollment(self, user: User, cohort_id: UUID) -> CohortMember:
        member = self._cohort_enrollment(user, cohort_id)
        if not member or member.role != CohortMemberRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this cohort")
        return member

    def _require_instructor_access(self, user: User, cohort_id: UUID) -> None:
        if user.role in {UserRole.ADMIN, UserRole.OPERATIONS}:
            return
        member = self._cohort_enrollment(user, cohort_id)
        if not member or member.role not in {CohortMemberRole.INSTRUCTOR, CohortMemberRole.TA}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an instructor for this cohort")

    def _is_staff_preview(self, user: User) -> bool:
        """Admins/ops can browse any cohort's student view as a read-only preview."""
        return user.role in {UserRole.ADMIN, UserRole.OPERATIONS}

    # ---------- public / student ----------

    def list_programmes(self) -> list[ProgrammePublic]:
        rows = list(
            self.db.scalars(
                select(Programme)
                .where(Programme.status.in_([ProgrammeStatus.UPCOMING, ProgrammeStatus.ACTIVE]))
                .order_by(Programme.title)
            ).all()
        )
        return [ProgrammePublic.model_validate(row) for row in rows]

    def get_programme(self, slug: str) -> ProgrammeDetailPublic:
        programme = self._get_programme(slug)
        cohorts = list(
            self.db.scalars(
                select(Cohort)
                .where(Cohort.programme_id == programme.id)
                .order_by(Cohort.starts_at.asc().nulls_last())
            ).all()
        )
        return ProgrammeDetailPublic(
            **ProgrammePublic.model_validate(programme).model_dump(),
            cohorts=[ProgrammeCohortPublic.model_validate(c) for c in cohorts],
        )

    def my_live_enrollments(self, user: User) -> list[MyLiveEnrollmentPublic]:
        if self._is_staff_preview(user):
            return self._preview_enrollments(user)

        memberships = list(
            self.db.scalars(
                select(CohortMember)
                .options(selectinload(CohortMember.cohort).joinedload(Cohort.programme))
                .where(
                    CohortMember.user_id == user.id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
            ).all()
        )
        results: list[MyLiveEnrollmentPublic] = []
        for member in memberships:
            cohort = member.cohort
            sessions = self._sessions(cohort.id)
            attendance = self._attendance_summary([s.id for s in sessions], user_id=user.id)
            next_session = self._next_session(sessions)
            results.append(
                MyLiveEnrollmentPublic(
                    programme_id=cohort.programme.id if cohort.programme else None,
                    programme_slug=cohort.programme.slug if cohort.programme else None,
                    programme_title=cohort.programme.title if cohort.programme else None,
                    cohort_id=cohort.id,
                    cohort_name=cohort.name,
                    cohort_slug=cohort.slug,
                    enrollment_status=member.enrollment_status.value,
                    starts_at=cohort.starts_at,
                    ends_at=cohort.ends_at,
                    timezone=cohort.timezone or "UTC",
                    progress_percent=self._progress_percent(user.id, cohort.id),
                    attendance_attended=attendance.attended + attendance.late,
                    attendance_total=len(sessions),
                    next_session=self.classroom._to_public(
                        next_session, member=member, staff=False, user=user
                    )
                    if next_session
                    else None,
                )
            )
        return results

    def _preview_enrollments(self, user: User) -> list[MyLiveEnrollmentPublic]:
        """All open/active cohorts for admin/ops, flagged as read-only previews."""
        cohorts = list(
            self.db.scalars(
                select(Cohort)
                .options(selectinload(Cohort.programme))
                .where(Cohort.status.in_([CohortStatus.OPEN, CohortStatus.ACTIVE]))
                .order_by(Cohort.starts_at.asc().nulls_last())
            )
            .unique()
            .all()
        )
        results: list[MyLiveEnrollmentPublic] = []
        for cohort in cohorts:
            sessions = self._sessions(cohort.id)
            next_session = self._next_session(sessions)
            results.append(
                MyLiveEnrollmentPublic(
                    programme_id=cohort.programme.id if cohort.programme else None,
                    programme_slug=cohort.programme.slug if cohort.programme else None,
                    programme_title=cohort.programme.title if cohort.programme else None,
                    cohort_id=cohort.id,
                    cohort_name=cohort.name,
                    cohort_slug=cohort.slug,
                    enrollment_status="preview",
                    starts_at=cohort.starts_at,
                    ends_at=cohort.ends_at,
                    timezone=cohort.timezone or "UTC",
                    progress_percent=0,
                    attendance_attended=0,
                    attendance_total=len(sessions),
                    next_session=self.classroom._to_public(
                        next_session, member=None, staff=False, user=user
                    )
                    if next_session
                    else None,
                    is_preview=True,
                )
            )
        return results

    def get_cohort_for_student(self, user: User, cohort_id: UUID) -> CohortStudentDetailPublic:
        if self._is_staff_preview(user):
            return self._preview_cohort(user, cohort_id)

        member = self._require_student_enrollment(user, cohort_id)
        cohort = self._get_cohort(cohort_id)
        sessions = self._sessions(cohort_id)
        recordings = self.classroom._recordings_for([s.id for s in sessions])
        attendance = self._attendance_summary([s.id for s in sessions], user_id=user.id)
        return CohortStudentDetailPublic(
            id=cohort.id,
            name=cohort.name,
            slug=cohort.slug,
            description=cohort.description or "",
            status=cohort.status.value,
            starts_at=cohort.starts_at,
            ends_at=cohort.ends_at,
            timezone=cohort.timezone or "UTC",
            capacity=cohort.capacity,
            community_links=cohort.community_links or {},
            programme=ProgrammePublic.model_validate(cohort.programme) if cohort.programme else None,
            progress_percent=self._progress_percent(user.id, cohort_id),
            attendance=attendance,
            sessions=[
                self.classroom._to_public(
                    s, member=member, staff=False, user=user, recordings=recordings
                )
                for s in sessions
            ],
        )

    def _preview_cohort(self, user: User, cohort_id: UUID) -> CohortStudentDetailPublic:
        """Read-only student-view preview for admins/ops (no enrollment required)."""
        cohort = self._get_cohort(cohort_id)
        sessions = self._sessions(cohort_id)
        recordings = self.classroom._recordings_for([s.id for s in sessions])
        return CohortStudentDetailPublic(
            id=cohort.id,
            name=cohort.name,
            slug=cohort.slug,
            description=cohort.description or "",
            status=cohort.status.value,
            starts_at=cohort.starts_at,
            ends_at=cohort.ends_at,
            timezone=cohort.timezone or "UTC",
            capacity=cohort.capacity,
            community_links=cohort.community_links or {},
            programme=ProgrammePublic.model_validate(cohort.programme) if cohort.programme else None,
            progress_percent=0,
            attendance=AttendanceSummaryPublic(),
            sessions=[
                self.classroom._to_public(
                    s, member=None, staff=False, user=user, recordings=recordings
                )
                for s in sessions
            ],
            is_preview=True,
        )

    def my_attendance(self, user: User, cohort_id: UUID) -> list[AttendanceRecordPublic]:
        self._require_student_enrollment(user, cohort_id)
        sessions = self._sessions(cohort_id)
        session_by_id = {s.id: s for s in sessions}
        rows = list(
            self.db.scalars(
                select(Attendance).where(
                    Attendance.user_id == user.id,
                    Attendance.session_id.in_([s.id for s in sessions]),
                )
            ).all()
        )
        return [
            AttendanceRecordPublic(
                session_id=row.session_id,
                session_title=session_by_id[row.session_id].title if row.session_id in session_by_id else "",
                starts_at=session_by_id[row.session_id].starts_at if row.session_id in session_by_id else row.recorded_at,
                status=row.status.value,
                recorded_at=row.recorded_at,
                note=row.note,
            )
            for row in rows
        ]


    # ---------- instructor / admin ----------

    def list_instructor_cohorts(self, user: User) -> list[CohortStudentDetailPublic]:
        if user.role in {UserRole.ADMIN, UserRole.OPERATIONS}:
            cohorts = list(self.db.scalars(select(Cohort).order_by(Cohort.starts_at.desc().nulls_last())).all())
        else:
            memberships = list(
                self.db.scalars(
                    select(CohortMember).where(
                        CohortMember.user_id == user.id,
                        CohortMember.role.in_([CohortMemberRole.INSTRUCTOR, CohortMemberRole.TA]),
                    )
                ).all()
            )
            cohort_ids = [m.cohort_id for m in memberships]
            cohorts = (
                list(self.db.scalars(select(Cohort).where(Cohort.id.in_(cohort_ids))).all())
                if cohort_ids
                else []
            )

        result: list[CohortStudentDetailPublic] = []
        for cohort in cohorts:
            sessions = self._sessions(cohort.id)
            result.append(
                CohortStudentDetailPublic(
                    id=cohort.id,
                    name=cohort.name,
                    slug=cohort.slug,
                    description=cohort.description or "",
                    status=cohort.status.value,
                    starts_at=cohort.starts_at,
                    ends_at=cohort.ends_at,
                    timezone=cohort.timezone or "UTC",
                    capacity=cohort.capacity,
                    community_links=cohort.community_links or {},
                    programme=ProgrammePublic.model_validate(cohort.programme) if cohort.programme else None,
                    progress_percent=0,
                    attendance=self._attendance_summary([s.id for s in sessions]),
                    sessions=[],
                )
            )
        return result

    def list_cohort_students(self, user: User, cohort_id: UUID) -> list[InstructorStudentRow]:
        self._require_instructor_access(user, cohort_id)
        members = list(
            self.db.scalars(
                select(CohortMember)
                .options(selectinload(CohortMember.user))
                .where(
                    CohortMember.cohort_id == cohort_id,
                    CohortMember.role == CohortMemberRole.STUDENT,
                )
                .order_by(CohortMember.joined_at.desc())
            ).all()
        )
        sessions = self._sessions(cohort_id)
        rows: list[InstructorStudentRow] = []
        for member in members:
            attendance = self._attendance_summary([s.id for s in sessions], user_id=member.user_id)
            rows.append(
                InstructorStudentRow(
                    user_id=member.user_id,
                    email=member.user.email,
                    full_name=member.user.full_name,
                    country_of_residence=member.user.country_of_residence,
                    enrollment_status=member.enrollment_status.value,
                    attendance_attended=attendance.attended + attendance.late,
                    attendance_total=len(sessions),
                    progress_percent=self._progress_percent(member.user_id, cohort_id),
                )
            )
        return rows

    def get_cohort_attendance(self, user: User, cohort_id: UUID) -> list[AttendanceRecordPublic]:
        self._require_instructor_access(user, cohort_id)
        sessions = self._sessions(cohort_id)
        session_by_id = {s.id: s for s in sessions}
        rows = list(
            self.db.scalars(
                select(Attendance).where(Attendance.session_id.in_([s.id for s in sessions]))
            ).all()
        )
        return [
            AttendanceRecordPublic(
                session_id=row.session_id,
                session_title=session_by_id[row.session_id].title if row.session_id in session_by_id else "",
                starts_at=session_by_id[row.session_id].starts_at if row.session_id in session_by_id else row.recorded_at,
                status=row.status.value,
                recorded_at=row.recorded_at,
                note=row.note,
            )
            for row in rows
        ]

    def record_attendance(
        self, user: User, cohort_id: UUID, payload: AttendanceBulkWrite
    ) -> list[AttendanceRecordPublic]:
        self._require_instructor_access(user, cohort_id)
        sessions = self._sessions(cohort_id)
        session_ids = {s.id for s in sessions}
        now = _utcnow()
        for item in payload.items:
            if item.session_id not in session_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session not in this cohort")
            student = self.db.get(User, item.user_id)
            if not student or student.role != UserRole.STUDENT:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student")
            existing = self.db.scalar(
                select(Attendance).where(
                    Attendance.session_id == item.session_id,
                    Attendance.user_id == item.user_id,
                )
            )
            if existing:
                existing.status = AttendanceStatus(item.status)
                existing.note = item.note
                existing.recorded_by = user.id
                existing.recorded_at = now
            else:
                self.db.add(
                    Attendance(
                        session_id=item.session_id,
                        user_id=item.user_id,
                        status=AttendanceStatus(item.status),
                        recorded_by=user.id,
                        note=item.note,
                    )
                )
        self.db.commit()
        return self.get_cohort_attendance(user, cohort_id)


    # ---------- admin CRUD ----------

    def create_programme(self, payload: ProgrammeUpsert) -> ProgrammePublic:
        existing = self.db.scalar(select(Programme).where(Programme.slug == payload.slug))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Programme slug already exists")
        programme = Programme(
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            overview=payload.overview,
            learning_outcomes=payload.learning_outcomes,
            duration=payload.duration,
            programme_type=payload.programme_type,
            status=ProgrammeStatus(payload.status),
            cover_image=payload.cover_image,
            requirements=payload.requirements,
            certificate_requirements=payload.certificate_requirements,
            course_id=payload.course_id,
        )
        self.db.add(programme)
        self.db.commit()
        self.db.refresh(programme)
        return ProgrammePublic.model_validate(programme)

    def update_programme(self, programme_id: UUID, payload: ProgrammeUpsert) -> ProgrammePublic:
        programme = self.db.get(Programme, programme_id)
        if not programme:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme not found")
        data = payload.model_dump()
        for field in ("slug", "title", "description", "overview", "duration", "programme_type", "cover_image", "course_id"):
            setattr(programme, field, data[field])
        programme.learning_outcomes = data["learning_outcomes"]
        programme.requirements = data["requirements"]
        programme.certificate_requirements = data["certificate_requirements"]
        programme.status = ProgrammeStatus(data["status"])
        self.db.commit()
        self.db.refresh(programme)
        return ProgrammePublic.model_validate(programme)

    def create_cohort(self, payload: CohortAdminUpsert) -> CohortStudentDetailPublic:
        existing = self.db.scalar(select(Cohort).where(Cohort.slug == payload.slug))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cohort slug already exists")
        cohort = Cohort(
            programme_id=payload.programme_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            status=CohortStatus(payload.status),
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            registration_deadline=payload.registration_deadline,
            timezone=payload.timezone or "UTC",
            capacity=payload.capacity,
            price=payload.price,
            currency=payload.currency.upper(),
            community_links=payload.community_links,
        )
        self.db.add(cohort)
        self.db.commit()
        self.db.refresh(cohort)
        return CohortStudentDetailPublic(
            id=cohort.id,
            name=cohort.name,
            slug=cohort.slug,
            description=cohort.description or "",
            status=cohort.status.value,
            starts_at=cohort.starts_at,
            ends_at=cohort.ends_at,
            timezone=cohort.timezone or "UTC",
            capacity=cohort.capacity,
            community_links=cohort.community_links or {},
            programme=ProgrammePublic.model_validate(cohort.programme) if cohort.programme else None,
            progress_percent=0,
            attendance=AttendanceSummaryPublic(),
            sessions=[],
        )

