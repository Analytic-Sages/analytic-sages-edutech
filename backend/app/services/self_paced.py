from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.payments import EnrollmentStatus
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lms import CourseModule, Lesson, LessonProgress
from app.models.user import User
from app.schemas.self_paced import (
    AdminCourseAnalytics,
    AdminCourseRow,
    CourseProgressPublic,
    EnrollResponse,
    EnrollmentWithProgress,
    LessonCompleteResponse,
    LessonDetailPublic,
    LessonOutlinePublic,
    LessonResourcePublic,
    ModuleOutlinePublic,
    SelfPacedCourseCard,
    SelfPacedCoursePublic,
)


class SelfPacedService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _utcnow(self) -> datetime:
        return datetime.now(UTC)

    def _curriculum_query(self):
        return (
            select(Course)
            .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
            .where(Course.published.is_(True), Course.delivery_type == "self_paced")
        )

    def _has_published_lessons(self, course: Course) -> bool:
        return any(lesson.published for module in course.modules for lesson in module.lessons)

    def _published_lessons(self, course: Course) -> list[Lesson]:
        lessons: list[Lesson] = []
        for module in sorted(course.modules, key=lambda item: item.order_index):
            for lesson in sorted(module.lessons, key=lambda item: item.order_index):
                if lesson.published:
                    lessons.append(lesson)
        return lessons

    def _get_course_by_slug(self, slug: str, *, require_curriculum: bool = True) -> Course:
        course = self.db.scalar(self._curriculum_query().where(Course.slug == slug))
        if not course or (require_curriculum and not self._has_published_lessons(course)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    def _active_enrollment(self, user: User, course_id: UUID) -> Enrollment | None:
        return self.db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id,
                Enrollment.course_id == course_id,
                Enrollment.status.in_((EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED)),
            )
        )

    def _require_enrollment(self, user: User, course: Course) -> Enrollment:
        enrollment = self._active_enrollment(user, course.id)
        if enrollment:
            return enrollment
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enroll in this course to access lessons",
        )

    def _progress_map(self, enrollment: Enrollment | None) -> dict[UUID, LessonProgress]:
        if not enrollment:
            return {}
        rows = self.db.scalars(
            select(LessonProgress).where(LessonProgress.enrollment_id == enrollment.id)
        ).all()
        return {row.lesson_id: row for row in rows}

    def _progress_stats(
        self, course: Course, enrollment: Enrollment | None
    ) -> tuple[int, int, int, str | None, list[str]]:
        lessons = self._published_lessons(course)
        total = len(lessons)
        progress = self._progress_map(enrollment)
        completed_lessons = [
            lesson for lesson in lessons if progress.get(lesson.id) and progress[lesson.id].completed
        ]
        completed_count = len(completed_lessons)
        percent = round((completed_count / total) * 100) if total else 0

        resume_slug: str | None = None
        if enrollment and lessons:
            viewed = [row for row in progress.values() if row.last_viewed_at]
            if viewed:
                latest = max(
                    viewed, key=lambda row: row.last_viewed_at or datetime.min.replace(tzinfo=UTC)
                )
                lesson = next((item for item in lessons if item.id == latest.lesson_id), None)
                if lesson:
                    resume_slug = lesson.slug
            if not resume_slug:
                incomplete = next(
                    (lesson for lesson in lessons if lesson not in completed_lessons), None
                )
                resume_slug = (incomplete or lessons[0]).slug

        return (
            completed_count,
            total,
            percent,
            resume_slug,
            [lesson.slug for lesson in completed_lessons],
        )

    def _card(self, course: Course) -> SelfPacedCourseCard:
        return SelfPacedCourseCard(
            id=course.id,
            slug=course.slug,
            title=course.title,
            description=course.description,
            thumbnail=course.thumbnail,
            category=course.category,
            difficulty=course.difficulty,
            duration=course.duration,
            estimated_minutes=course.estimated_minutes,
            lessons_count=course.lessons_count,
            price=course.price,
            currency=course.currency,
            is_free=course.is_free,
            delivery_type=course.delivery_type,
            certificate_enabled=course.certificate_enabled,
        )

    def _outline(
        self,
        course: Course,
        enrollment: Enrollment | None,
        *,
        include_video_ids: bool,
    ) -> list[ModuleOutlinePublic]:
        progress = self._progress_map(enrollment)
        modules: list[ModuleOutlinePublic] = []
        for module in sorted(course.modules, key=lambda item: item.order_index):
            lessons: list[LessonOutlinePublic] = []
            for lesson in sorted(module.lessons, key=lambda item: item.order_index):
                if not lesson.published:
                    continue
                record = progress.get(lesson.id)
                lessons.append(
                    LessonOutlinePublic(
                        id=lesson.id,
                        slug=lesson.slug,
                        title=lesson.title,
                        subtitle=lesson.subtitle,
                        duration_seconds=lesson.duration_seconds,
                        order_index=lesson.order_index,
                        video_provider=lesson.video_provider,
                        video_id=lesson.video_id if include_video_ids else None,
                        completed=bool(record and record.completed),
                    )
                )
            modules.append(
                ModuleOutlinePublic(
                    id=module.id,
                    title=module.title,
                    description=module.description,
                    order_index=module.order_index,
                    lessons=lessons,
                )
            )
        return modules

    def _course_public(
        self,
        course: Course,
        user: User | None,
        *,
        include_video_ids: bool,
    ) -> SelfPacedCoursePublic:
        enrollment = self._active_enrollment(user, course.id) if user else None
        completed_count, total, percent, resume_slug, _ = self._progress_stats(course, enrollment)
        return SelfPacedCoursePublic(
            **self._card(course).model_dump(),
            long_description=course.long_description or course.description,
            published=course.published,
            enrolled=enrollment is not None,
            completed=bool(enrollment and enrollment.completed_at),
            progress_percent=percent,
            lessons_completed=completed_count,
            resume_lesson_slug=resume_slug,
            modules=self._outline(course, enrollment, include_video_ids=include_video_ids),
        )

    def list_catalog(self) -> list[SelfPacedCourseCard]:
        courses = list(self.db.scalars(self._curriculum_query().order_by(Course.title)).all())
        return [self._card(course) for course in courses if self._has_published_lessons(course)]

    def get_public_course(self, slug: str, user: User | None) -> SelfPacedCoursePublic:
        course = self._get_course_by_slug(slug)
        return self._course_public(course, user, include_video_ids=True)

    def enroll_free(self, user: User, slug: str) -> EnrollResponse:
        course = self._get_course_by_slug(slug)
        if not course.is_free or course.price > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This course requires checkout",
            )

        existing = self.db.scalar(
            select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == course.id)
        )
        now = self._utcnow()
        already = False
        if existing:
            already = True
            if existing.status == EnrollmentStatus.REVOKED:
                existing.status = EnrollmentStatus.ACTIVE
                existing.enrolled_at = now
                already = False
            existing.last_activity_at = now
            enrollment = existing
        else:
            enrollment = Enrollment(
                user_id=user.id,
                course_id=course.id,
                status=EnrollmentStatus.ACTIVE,
                last_activity_at=now,
            )
            self.db.add(enrollment)
            try:
                self.db.flush()
            except IntegrityError as exc:
                self.db.rollback()
                enrollment = self.db.scalar(
                    select(Enrollment).where(
                        Enrollment.user_id == user.id,
                        Enrollment.course_id == course.id,
                    )
                )
                if not enrollment:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Could not create enrollment",
                    ) from exc
                already = True

        self.db.commit()
        self.db.refresh(enrollment)
        course = self._get_course_by_slug(slug)
        _, _, _, resume_slug, _ = self._progress_stats(course, enrollment)
        return EnrollResponse(
            enrollment_id=enrollment.id,
            course_slug=course.slug,
            already_enrolled=already,
            resume_lesson_slug=resume_slug,
            status=enrollment.status.value,
        )

    def get_learn_course(self, user: User, slug: str) -> SelfPacedCoursePublic:
        course = self._get_course_by_slug(slug)
        self._require_enrollment(user, course)
        return self._course_public(course, user, include_video_ids=True)

    def get_progress(self, user: User, slug: str) -> CourseProgressPublic:
        course = self._get_course_by_slug(slug)
        enrollment = self._require_enrollment(user, course)
        completed_count, total, percent, resume_slug, completed_slugs = self._progress_stats(
            course, enrollment
        )
        return CourseProgressPublic(
            course_id=course.id,
            course_slug=course.slug,
            enrollment_id=enrollment.id,
            status=enrollment.status.value,
            enrolled_at=enrollment.enrolled_at,
            completed_at=enrollment.completed_at,
            last_activity_at=enrollment.last_activity_at,
            progress_percent=percent,
            lessons_completed=completed_count,
            lessons_total=total,
            resume_lesson_slug=resume_slug,
            completed_lesson_slugs=completed_slugs,
        )

    def _touch_view(self, enrollment: Enrollment, lesson: Lesson) -> LessonProgress:
        record = self.db.scalar(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson.id,
            )
        )
        now = self._utcnow()
        if record:
            record.last_viewed_at = now
        else:
            record = LessonProgress(
                enrollment_id=enrollment.id,
                lesson_id=lesson.id,
                last_viewed_at=now,
            )
            self.db.add(record)
        enrollment.last_activity_at = now
        return record

    def _as_resources(self, raw: object) -> list[LessonResourcePublic]:
        if not isinstance(raw, list):
            return []
        items: list[LessonResourcePublic] = []
        for entry in raw:
            if isinstance(entry, dict) and entry.get("label") and entry.get("url"):
                items.append(LessonResourcePublic(label=str(entry["label"]), url=str(entry["url"])))
        return items

    def get_lesson(self, user: User, course_slug: str, lesson_slug: str) -> LessonDetailPublic:
        course = self._get_course_by_slug(course_slug)
        enrollment = self._require_enrollment(user, course)
        lessons = self._published_lessons(course)
        lesson = next((item for item in lessons if item.slug == lesson_slug), None)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        self._touch_view(enrollment, lesson)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            course = self._get_course_by_slug(course_slug)
            enrollment = self._require_enrollment(user, course)
            lesson = next((item for item in self._published_lessons(course) if item.slug == lesson_slug))
            self._touch_view(enrollment, lesson)
            self.db.commit()

        lessons = self._published_lessons(course)
        completed_count, total, percent, _, _ = self._progress_stats(course, enrollment)
        index = next(i for i, item in enumerate(lessons) if item.slug == lesson_slug)
        lesson = lessons[index]
        progress = self._progress_map(enrollment)
        record = progress.get(lesson.id)
        return LessonDetailPublic(
            id=lesson.id,
            slug=lesson.slug,
            title=lesson.title,
            subtitle=lesson.subtitle,
            description=lesson.description,
            module_id=lesson.module_id,
            module_title=lesson.module.title,
            lesson_number=index + 1,
            lessons_total=total,
            duration_seconds=lesson.duration_seconds,
            video_provider=lesson.video_provider,
            video_id=lesson.video_id,
            what_you_learn=list(lesson.what_you_learn or []),
            key_concepts=list(lesson.key_concepts or []),
            resources=self._as_resources(lesson.resources),
            completed=bool(record and record.completed),
            prev_slug=lessons[index - 1].slug if index > 0 else None,
            next_slug=lessons[index + 1].slug if index + 1 < len(lessons) else None,
            course_title=course.title,
            course_slug=course.slug,
            course_completed=bool(enrollment.completed_at),
            progress_percent=percent,
            lessons_completed=completed_count,
        )

    def _sync_course_completion(self, course: Course, enrollment: Enrollment) -> None:
        completed_count, total, _, _, _ = self._progress_stats(course, enrollment)
        if total > 0 and completed_count >= total:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = enrollment.completed_at or self._utcnow()

    def complete_lesson(
        self, user: User, course_slug: str, lesson_slug: str
    ) -> LessonCompleteResponse:
        course = self._get_course_by_slug(course_slug)
        enrollment = self._require_enrollment(user, course)
        lessons = self._published_lessons(course)
        lesson = next((item for item in lessons if item.slug == lesson_slug), None)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

        record = self.db.scalar(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson.id,
            )
        )
        now = self._utcnow()
        if record:
            if not record.completed:
                record.completed = True
                record.completed_at = now
            record.last_viewed_at = now
        else:
            record = LessonProgress(
                enrollment_id=enrollment.id,
                lesson_id=lesson.id,
                completed=True,
                completed_at=now,
                last_viewed_at=now,
            )
            self.db.add(record)
        enrollment.last_activity_at = now
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            course = self._get_course_by_slug(course_slug)
            enrollment = self._require_enrollment(user, course)
            lesson = next(item for item in self._published_lessons(course) if item.slug == lesson_slug)
            record = self.db.scalar(
                select(LessonProgress).where(
                    LessonProgress.enrollment_id == enrollment.id,
                    LessonProgress.lesson_id == lesson.id,
                )
            )
            if record and not record.completed:
                record.completed = True
                record.completed_at = now
            enrollment.last_activity_at = now

        self._sync_course_completion(course, enrollment)
        self.db.commit()
        self.db.refresh(enrollment)

        lessons = self._published_lessons(course)
        completed_count, total, percent, _, _ = self._progress_stats(course, enrollment)
        index = next(i for i, item in enumerate(lessons) if item.slug == lesson_slug)
        return LessonCompleteResponse(
            lesson_slug=lesson_slug,
            completed=True,
            course_completed=bool(enrollment.completed_at),
            progress_percent=percent,
            lessons_completed=completed_count,
            lessons_total=total,
            next_slug=lessons[index + 1].slug if index + 1 < len(lessons) else None,
        )

    def list_my_enrollments(self, user: User) -> list[EnrollmentWithProgress]:
        enrollments = list(
            self.db.scalars(
                select(Enrollment)
                .options(
                    joinedload(Enrollment.course)
                    .selectinload(Course.modules)
                    .selectinload(CourseModule.lessons)
                )
                .where(
                    Enrollment.user_id == user.id,
                    Enrollment.status.in_((EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED)),
                )
                .order_by(Enrollment.enrolled_at.desc())
            ).unique()
        )
        results: list[EnrollmentWithProgress] = []
        for enrollment in enrollments:
            course = enrollment.course
            completed_count, total, percent, resume_slug, _ = self._progress_stats(course, enrollment)
            results.append(
                EnrollmentWithProgress(
                    id=enrollment.id,
                    course_id=enrollment.course_id,
                    status=enrollment.status.value,
                    enrolled_at=enrollment.enrolled_at,
                    completed_at=enrollment.completed_at,
                    last_activity_at=enrollment.last_activity_at,
                    progress_percent=percent,
                    lessons_completed=completed_count,
                    lessons_total=total,
                    resume_lesson_slug=resume_slug,
                    course=self._card(course),
                )
            )
        return results

    def list_admin_courses(self) -> list[AdminCourseRow]:
        courses = list(
            self.db.scalars(
                select(Course)
                .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
                .order_by(Course.title)
            ).all()
        )
        return [self._admin_row(course) for course in courses]

    def course_analytics(self, slug: str) -> AdminCourseAnalytics:
        course = self.db.scalar(
            select(Course)
            .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
            .where(Course.slug == slug)
        )
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        row = self._admin_row(course)
        enrollments = list(
            self.db.scalars(select(Enrollment).where(Enrollment.course_id == course.id)).all()
        )
        counted = [
            item
            for item in enrollments
            if item.status in {EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED}
        ]
        if counted:
            lessons_completed = int(
                self.db.scalar(
                    select(func.count(LessonProgress.id)).where(
                        LessonProgress.completed.is_(True),
                        LessonProgress.enrollment_id.in_([item.id for item in counted]),
                    )
                )
                or 0
            )
        else:
            lessons_completed = 0
        completion_rate = (
            round((row.completions_count / row.enrollments_count) * 100, 1)
            if row.enrollments_count
            else 0.0
        )
        last_activity = max(
            (item.last_activity_at for item in counted if item.last_activity_at), default=None
        )
        return AdminCourseAnalytics(
            course=row,
            enrollments_count=row.enrollments_count,
            active_learners=sum(1 for item in counted if item.status == EnrollmentStatus.ACTIVE),
            lessons_completed=lessons_completed,
            completion_rate=completion_rate,
            avg_progress_percent=row.avg_progress_percent,
            last_activity_at=last_activity,
        )

    def _admin_row(self, course: Course) -> AdminCourseRow:
        enrollments = list(
            self.db.scalars(select(Enrollment).where(Enrollment.course_id == course.id)).all()
        )
        counted = [
            item
            for item in enrollments
            if item.status in {EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED}
        ]
        percents: list[int] = []
        for enrollment in counted:
            _, _, percent, _, _ = self._progress_stats(course, enrollment)
            percents.append(percent)
        avg = round(sum(percents) / len(percents)) if percents else 0
        last_activity = max(
            (item.last_activity_at for item in counted if item.last_activity_at), default=None
        )
        return AdminCourseRow(
            id=course.id,
            slug=course.slug,
            title=course.title,
            published=course.published,
            is_free=course.is_free,
            delivery_type=course.delivery_type,
            price=course.price,
            currency=course.currency,
            lessons_count=len(self._published_lessons(course)),
            modules_count=len(course.modules),
            enrollments_count=len(counted),
            completions_count=sum(1 for item in counted if item.completed_at),
            avg_progress_percent=avg,
            last_activity_at=last_activity,
        )
