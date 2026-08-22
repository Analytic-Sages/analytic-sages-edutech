from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.classroom import Cohort
from app.models.course import Course
from app.models.instructor import CohortInstructor, CourseInstructor, InstructorProfile
from app.schemas.instructors import (
    AdminCohortInstructorRow,
    InstructorAssignmentItem,
    InstructorProfileAdmin,
    InstructorProfileWrite,
    InstructorPublic,
)


class InstructorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _normalize_bullets(self, bullets: list[str]) -> list[str]:
        return [item.strip() for item in bullets if item.strip()][:5]

    def _to_public(self, link: CourseInstructor | CohortInstructor) -> InstructorPublic:
        profile = link.instructor
        bullets = [str(item).strip() for item in (profile.bullets or []) if str(item).strip()]
        return InstructorPublic(
            id=profile.id,
            name=profile.name,
            title=profile.title or "",
            photo_url=profile.photo_url,
            bullets=bullets[:5],
            role_label=link.role_label or "Instructor",
            sort_order=link.sort_order,
        )

    def _admin_profile(self, profile: InstructorProfile) -> InstructorProfileAdmin:
        bullets = [str(item).strip() for item in (profile.bullets or []) if str(item).strip()]
        return InstructorProfileAdmin(
            id=profile.id,
            name=profile.name,
            title=profile.title or "",
            photo_url=profile.photo_url,
            bullets=bullets[:5],
            course_count=len(profile.course_links),
            cohort_count=len(profile.cohort_links),
        )

    def _get_profile(self, instructor_id: UUID) -> InstructorProfile:
        profile = self.db.get(InstructorProfile, instructor_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")
        return profile

    def _get_course(self, slug: str) -> Course:
        course = self.db.scalar(select(Course).where(Course.slug == slug))
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    def _get_cohort(self, slug: str) -> Cohort:
        cohort = self.db.scalar(select(Cohort).where(Cohort.slug == slug))
        if not cohort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
        return cohort

    def list_profiles(self) -> list[InstructorProfileAdmin]:
        profiles = list(
            self.db.scalars(
                select(InstructorProfile)
                .options(
                    selectinload(InstructorProfile.course_links),
                    selectinload(InstructorProfile.cohort_links),
                )
                .order_by(InstructorProfile.name)
            ).all()
        )
        return [self._admin_profile(item) for item in profiles]

    def create_profile(self, payload: InstructorProfileWrite) -> InstructorProfileAdmin:
        profile = InstructorProfile(
            name=payload.name,
            title=payload.title,
            photo_url=payload.photo_url,
            bullets=self._normalize_bullets(payload.bullets),
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return self._admin_profile(self._get_profile(profile.id))

    def update_profile(
        self, instructor_id: UUID, payload: InstructorProfileWrite
    ) -> InstructorProfileAdmin:
        profile = self._get_profile(instructor_id)
        profile.name = payload.name
        profile.title = payload.title
        profile.photo_url = payload.photo_url
        profile.bullets = self._normalize_bullets(payload.bullets)
        self.db.commit()
        return self._admin_profile(self._get_profile(instructor_id))

    def delete_profile(self, instructor_id: UUID) -> None:
        profile = self._get_profile(instructor_id)
        self.db.delete(profile)
        self.db.commit()

    def list_for_course(self, course_id: UUID) -> list[InstructorPublic]:
        links = list(
            self.db.scalars(
                select(CourseInstructor)
                .options(selectinload(CourseInstructor.instructor))
                .where(CourseInstructor.course_id == course_id)
                .order_by(CourseInstructor.sort_order, CourseInstructor.id)
            ).all()
        )
        return [self._to_public(link) for link in links]

    def list_for_cohort(self, cohort: Cohort) -> list[InstructorPublic]:
        cohort_links = list(
            self.db.scalars(
                select(CohortInstructor)
                .options(selectinload(CohortInstructor.instructor))
                .where(CohortInstructor.cohort_id == cohort.id)
                .order_by(CohortInstructor.sort_order, CohortInstructor.id)
            ).all()
        )
        if cohort_links:
            return [self._to_public(link) for link in cohort_links]
        if cohort.course_id:
            return self.list_for_course(cohort.course_id)
        return []

    def list_course_assignments(self, slug: str) -> list[InstructorPublic]:
        course = self._get_course(slug)
        return self.list_for_course(course.id)

    def list_cohort_assignments(self, slug: str) -> list[InstructorPublic]:
        cohort = self._get_cohort(slug)
        links = list(
            self.db.scalars(
                select(CohortInstructor)
                .options(selectinload(CohortInstructor.instructor))
                .where(CohortInstructor.cohort_id == cohort.id)
                .order_by(CohortInstructor.sort_order, CohortInstructor.id)
            ).all()
        )
        return [self._to_public(link) for link in links]

    def replace_course_assignments(
        self, slug: str, items: list[InstructorAssignmentItem]
    ) -> list[InstructorPublic]:
        course = self._get_course(slug)
        self._replace_links(
            existing=list(
                self.db.scalars(
                    select(CourseInstructor).where(CourseInstructor.course_id == course.id)
                ).all()
            ),
            items=items,
            add=lambda item, order: CourseInstructor(
                course_id=course.id,
                instructor_id=item.instructor_id,
                role_label=item.role_label,
                sort_order=order,
            ),
        )
        self.db.commit()
        return self.list_for_course(course.id)

    def replace_cohort_assignments(
        self, slug: str, items: list[InstructorAssignmentItem]
    ) -> list[InstructorPublic]:
        cohort = self._get_cohort(slug)
        self._replace_links(
            existing=list(
                self.db.scalars(
                    select(CohortInstructor).where(CohortInstructor.cohort_id == cohort.id)
                ).all()
            ),
            items=items,
            add=lambda item, order: CohortInstructor(
                cohort_id=cohort.id,
                instructor_id=item.instructor_id,
                role_label=item.role_label,
                sort_order=order,
            ),
        )
        self.db.commit()
        return self.list_cohort_assignments(slug)

    def _replace_links(
        self,
        *,
        existing: list[CourseInstructor] | list[CohortInstructor],
        items: list[InstructorAssignmentItem],
        add,
    ) -> None:
        seen: set[UUID] = set()
        for item in items:
            if item.instructor_id in seen:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The same instructor cannot be added twice",
                )
            seen.add(item.instructor_id)
            self._get_profile(item.instructor_id)

        for row in existing:
            self.db.delete(row)
        self.db.flush()

        for index, item in enumerate(items):
            self.db.add(add(item, item.sort_order if item.sort_order else index))

    def list_admin_cohorts(self) -> list[AdminCohortInstructorRow]:
        cohorts = list(self.db.scalars(select(Cohort).order_by(Cohort.name)).all())
        counts = dict(
            self.db.execute(
                select(CohortInstructor.cohort_id, func.count(CohortInstructor.id)).group_by(
                    CohortInstructor.cohort_id
                )
            ).all()
        )
        return [
            AdminCohortInstructorRow(
                id=cohort.id,
                slug=cohort.slug,
                name=cohort.name,
                status=cohort.status.value,
                instructor_count=int(counts.get(cohort.id, 0)),
            )
            for cohort in cohorts
        ]

    def course_instructor_count(self, course_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count(CourseInstructor.id)).where(CourseInstructor.course_id == course_id)
            )
            or 0
        )
