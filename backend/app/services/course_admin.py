"""Admin CRUD for the self-paced LMS (courses, modules, lessons, resources).

Lets staff publish a new course without a developer: create the course, add modules
and lessons, upload downloadable resources, and attach a video (YouTube or
Cloudflare Stream). Publishing is a simple flag; the public learner API reads the
same models.
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.course import Course
from app.models.lms import CourseModule, Lesson
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
)

SLUG_SAFE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    slug = SLUG_SAFE.sub("-", value.strip().lower()).strip("-")
    return slug[:180] or "lesson"


class CourseAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------- helpers ----------

    def _get_course(self, slug: str) -> Course:
        course = self.db.scalar(
            select(Course)
            .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
            .where(Course.slug == slug)
        )
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    def _require_module(self, module_id: UUID) -> CourseModule:
        module = self.db.get(CourseModule, module_id)
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        return module

    def _require_lesson(self, lesson_id: UUID) -> Lesson:
        lesson = self.db.get(Lesson, lesson_id)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        return lesson

    def _next_module_order(self, course_id: UUID) -> int:
        current = self.db.scalar(
            select(func.coalesce(func.max(CourseModule.order_index), 0)).where(
                CourseModule.course_id == course_id
            )
        )
        return int(current or 0) + 1

    def _next_lesson_order(self, module_id: UUID) -> int:
        current = self.db.scalar(
            select(func.coalesce(func.max(Lesson.order_index), 0)).where(
                Lesson.module_id == module_id
            )
        )
        return int(current or 0) + 1

    def _sync_lessons_count(self, course: Course) -> None:
        count = self.db.scalar(
            select(func.count()).select_from(Lesson).where(Lesson.course_id == course.id)
        )
        course.lessons_count = int(count or 0)

    def _assert_module_order_free(
        self, *, course_id: UUID, order_index: int, exclude_id: UUID | None
    ) -> None:
        stmt = select(CourseModule).where(
            CourseModule.course_id == course_id,
            CourseModule.order_index == order_index,
        )
        if exclude_id:
            stmt = stmt.where(CourseModule.id != exclude_id)
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Module order {order_index} is already used",
            )

    def _assert_lesson_order_free(
        self, *, module_id: UUID, order_index: int, exclude_id: UUID | None
    ) -> None:
        stmt = select(Lesson).where(
            Lesson.module_id == module_id,
            Lesson.order_index == order_index,
        )
        if exclude_id:
            stmt = stmt.where(Lesson.id != exclude_id)
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lesson order {order_index} is already used in this module",
            )

    def _assert_unique_slug(self, *, course_id: UUID, slug: str, exclude_id: UUID | None) -> None:
        stmt = select(Lesson).where(Lesson.course_id == course_id, Lesson.slug == slug)
        if exclude_id:
            stmt = stmt.where(Lesson.id != exclude_id)
        if self.db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A lesson with slug '{slug}' already exists in this course",
            )

    # ---------- serialization ----------

    def _lesson_row(self, lesson: Lesson) -> AdminLessonRow:
        return AdminLessonRow(
            id=lesson.id,
            module_id=lesson.module_id,
            slug=lesson.slug,
            title=lesson.title,
            subtitle=lesson.subtitle,
            description=lesson.description,
            video_provider=lesson.video_provider,
            video_id=lesson.video_id,
            duration_seconds=lesson.duration_seconds,
            order_index=lesson.order_index,
            published=lesson.published,
            what_you_learn=list(lesson.what_you_learn or []),
            key_concepts=list(lesson.key_concepts or []),
            resources=list(lesson.resources or []),
        )

    def _module_row(self, module: CourseModule) -> AdminModuleRow:
        return AdminModuleRow(
            id=module.id,
            title=module.title,
            description=module.description,
            order_index=module.order_index,
            lessons=[
                self._lesson_row(lesson)
                for lesson in sorted(module.lessons, key=lambda item: item.order_index)
            ],
        )

    def _detail(self, course: Course) -> AdminCourseDetail:
        return AdminCourseDetail(
            id=course.id,
            slug=course.slug,
            title=course.title,
            description=course.description,
            long_description=course.long_description,
            thumbnail=course.thumbnail,
            category=course.category,
            difficulty=course.difficulty,
            duration=course.duration,
            lessons_count=course.lessons_count,
            price=course.price,
            currency=course.currency,
            delivery_type=course.delivery_type,
            is_free=course.is_free,
            certificate_enabled=course.certificate_enabled,
            published=course.published,
            modules=[
                self._module_row(module)
                for module in sorted(course.modules, key=lambda item: item.order_index)
            ],
        )

    # ---------- course CRUD ----------

    def get_course(self, slug: str) -> AdminCourseDetail:
        return self._detail(self._get_course(slug))

    def create_course(self, payload: AdminCourseUpsert) -> AdminCourseDetail:
        exists = self.db.scalar(select(Course).where(Course.slug == payload.slug))
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A course with slug '{payload.slug}' already exists",
            )
        data = payload.model_dump()
        course = Course(**data)
        if course.is_free or course.price == 0:
            course.is_free = True
        self.db.add(course)
        self.db.commit()
        return self._detail(self._get_course(course.slug))

    def update_course(self, slug: str, payload: AdminCourseUpdate) -> AdminCourseDetail:
        course = self._get_course(slug)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(course, field, value)
        if "price" in data or "is_free" in data:
            course.is_free = course.price == 0 or course.is_free
        self.db.commit()
        return self._detail(self._get_course(course.slug))

    def delete_course(self, slug: str) -> None:
        course = self._get_course(slug)
        self.db.delete(course)
        self.db.commit()

    # ---------- module CRUD ----------

    def create_module(self, slug: str, payload: AdminModuleUpsert) -> AdminModuleRow:
        course = self._get_course(slug)
        order = payload.order_index or self._next_module_order(course.id)
        self._assert_module_order_free(
            course_id=course.id, order_index=order, exclude_id=None
        )
        module = CourseModule(
            course_id=course.id,
            title=payload.title,
            description=payload.description,
            order_index=order,
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return self._module_row(module)

    def update_module(self, module_id: UUID, payload: AdminModuleUpdate) -> AdminModuleRow:
        module = self._require_module(module_id)
        data = payload.model_dump(exclude_unset=True)
        if "order_index" in data and data["order_index"] != module.order_index:
            self._assert_module_order_free(
                course_id=module.course_id,
                order_index=data["order_index"],
                exclude_id=module.id,
            )
        for field, value in data.items():
            setattr(module, field, value)
        self.db.commit()
        self.db.refresh(module)
        return self._module_row(module)

    def delete_module(self, module_id: UUID) -> None:
        module = self._require_module(module_id)
        course = self.db.get(Course, module.course_id)
        self.db.delete(module)
        self.db.flush()
        if course:
            self._sync_lessons_count(course)
        self.db.commit()

    # ---------- lesson CRUD ----------

    def create_lesson(self, module_id: UUID, payload: AdminLessonUpsert) -> AdminLessonRow:
        module = self._require_module(module_id)
        slug = payload.slug or slugify(payload.title)
        order = payload.order_index or self._next_lesson_order(module.id)
        self._assert_unique_slug(course_id=module.course_id, slug=slug, exclude_id=None)
        self._assert_lesson_order_free(
            module_id=module.id, order_index=order, exclude_id=None
        )
        lesson = Lesson(
            course_id=module.course_id,
            module_id=module.id,
            title=payload.title,
            slug=slug,
            subtitle=payload.subtitle,
            description=payload.description,
            video_provider=payload.video_provider,
            video_id=payload.video_id,
            duration_seconds=payload.duration_seconds,
            order_index=order,
            published=payload.published,
            what_you_learn=list(payload.what_you_learn),
            key_concepts=list(payload.key_concepts),
            resources=[],
        )
        self.db.add(lesson)
        self.db.flush()
        course = self.db.get(Course, module.course_id)
        if course:
            self._sync_lessons_count(course)
        self.db.commit()
        self.db.refresh(lesson)
        return self._lesson_row(lesson)

    def update_lesson(self, lesson_id: UUID, payload: AdminLessonUpdate) -> AdminLessonRow:
        lesson = self._require_lesson(lesson_id)
        data = payload.model_dump(exclude_unset=True)
        if "order_index" in data and data["order_index"] != lesson.order_index:
            self._assert_lesson_order_free(
                module_id=lesson.module_id,
                order_index=data["order_index"],
                exclude_id=lesson.id,
            )
        for field, value in data.items():
            setattr(lesson, field, value)
        self.db.commit()
        self.db.refresh(lesson)
        return self._lesson_row(lesson)

    def delete_lesson(self, lesson_id: UUID) -> None:
        lesson = self._require_lesson(lesson_id)
        course = self.db.get(Course, lesson.course_id)
        self.db.delete(lesson)
        self.db.flush()
        if course:
            self._sync_lessons_count(course)
        self.db.commit()

    def add_lesson_resource(
        self, lesson_id: UUID, payload: AdminLessonResourceUpsert
    ) -> AdminLessonRow:
        lesson = self._require_lesson(lesson_id)
        resources = list(lesson.resources or [])
        resources.append({"label": payload.label, "url": payload.url, "kind": payload.kind})
        lesson.resources = resources
        self.db.commit()
        self.db.refresh(lesson)
        return self._lesson_row(lesson)

    def remove_lesson_resource(self, lesson_id: UUID, url: str) -> AdminLessonRow:
        lesson = self._require_lesson(lesson_id)
        lesson.resources = [r for r in (lesson.resources or []) if r.get("url") != url]
        self.db.commit()
        self.db.refresh(lesson)
        return self._lesson_row(lesson)

    def set_lesson_video(self, lesson_id: UUID, *, provider: str, video_id: str) -> AdminLessonRow:
        lesson = self._require_lesson(lesson_id)
        lesson.video_provider = provider
        lesson.video_id = video_id
        self.db.commit()
        self.db.refresh(lesson)
        return self._lesson_row(lesson)

    def get_lesson(self, lesson_id: UUID) -> AdminLessonRow:
        return self._lesson_row(self._require_lesson(lesson_id))

    def list_video_ids(self) -> set[str]:
        """Existing Cloudflare Stream UIDs referenced by lessons (for the picker)."""
        rows = self.db.scalars(
            select(Lesson.video_id).where(
                Lesson.video_provider == "cloudflare_stream", Lesson.video_id.is_not(None)
            )
        ).all()
        return {str(v) for v in rows if v}