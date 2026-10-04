"""Admin CRUD for quizzes (author multiple-choice questions + answer keys)."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.course import Course
from app.models.lms import CourseModule, Lesson
from app.models.quiz import Quiz, QuizAttempt, QuizOption, QuizQuestion
from app.schemas.quizzes import (
    AdminQuizDetail,
    AdminQuizOption,
    AdminQuizQuestion,
    AdminQuizRow,
    QuizCreate,
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizUpdate,
)


class QuizAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_course(self, slug: str) -> Course:
        course = self.db.scalar(select(Course).where(Course.slug == slug))
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        return course

    def _get_quiz(self, quiz_id: UUID) -> Quiz:
        quiz = self.db.scalar(
            select(Quiz)
            .options(
                selectinload(Quiz.questions).selectinload(QuizQuestion.options),
                selectinload(Quiz.course),
            )
            .where(Quiz.id == quiz_id)
        )
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return quiz

    def _get_question(self, question_id: UUID) -> QuizQuestion:
        question = self.db.scalar(
            select(QuizQuestion)
            .options(selectinload(QuizQuestion.options))
            .where(QuizQuestion.id == question_id)
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
            )
        return question

    def _stats(self, quiz_id: UUID) -> tuple[int, float]:
        total = int(
            self.db.scalar(
                select(func.count())
                .select_from(QuizAttempt)
                .where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.completed_at.is_not(None))
            )
            or 0
        )
        if not total:
            return 0, 0.0
        passed = int(
            self.db.scalar(
                select(func.count())
                .select_from(QuizAttempt)
                .where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.passed.is_(True))
            )
            or 0
        )
        return total, round((passed / total) * 100, 1)

    def _row(self, quiz: Quiz) -> AdminQuizRow:
        attempts, pass_rate = self._stats(quiz.id)
        return AdminQuizRow(
            id=quiz.id,
            course_id=quiz.course_id,
            course_slug=quiz.course.slug if quiz.course else "",
            module_id=quiz.module_id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            description=quiz.description,
            pass_score=quiz.pass_score,
            published=quiz.published,
            order_index=quiz.order_index,
            questions_total=len(quiz.questions),
            attempts_count=attempts,
            pass_rate=pass_rate,
        )

    def _detail(self, quiz: Quiz) -> AdminQuizDetail:
        row = self._row(quiz)
        return AdminQuizDetail(
            **row.model_dump(),
            questions=[
                AdminQuizQuestion(
                    id=question.id,
                    prompt=question.prompt,
                    explanation=question.explanation,
                    order_index=question.order_index,
                    options=[
                        AdminQuizOption(
                            id=option.id,
                            label=option.label,
                            is_correct=option.is_correct,
                            order_index=option.order_index,
                        )
                        for option in sorted(question.options, key=lambda o: o.order_index)
                    ],
                )
                for question in sorted(quiz.questions, key=lambda q: q.order_index)
            ],
        )

    def list_quizzes(self, *, course_slug: str | None = None) -> list[AdminQuizRow]:
        stmt = (
            select(Quiz)
            .options(selectinload(Quiz.questions), selectinload(Quiz.course))
            .order_by(Quiz.order_index)
        )
        if course_slug:
            stmt = stmt.where(Quiz.course_id == self._get_course(course_slug).id)
        return [self._row(quiz) for quiz in self.db.scalars(stmt).all()]

    def get_quiz(self, quiz_id: UUID) -> AdminQuizDetail:
        return self._detail(self._get_quiz(quiz_id))

    def create_quiz(self, course_slug: str, payload: QuizCreate) -> AdminQuizDetail:
        course = self._get_course(course_slug)
        if payload.module_id:
            module = self.db.get(CourseModule, payload.module_id)
            if not module or module.course_id != course.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Module is not in this course"
                )
        if payload.lesson_id:
            lesson = self.db.get(Lesson, payload.lesson_id)
            if not lesson or lesson.course_id != course.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Lesson is not in this course"
                )
        order = payload.order_index or (
            int(
                self.db.scalar(
                    select(func.coalesce(func.max(Quiz.order_index), 0)).where(
                        Quiz.course_id == course.id
                    )
                )
                or 0
            )
            + 1
        )
        quiz = Quiz(
            course_id=course.id,
            module_id=payload.module_id,
            lesson_id=payload.lesson_id,
            title=payload.title,
            description=payload.description,
            pass_score=payload.pass_score,
            published=payload.published,
            order_index=order,
        )
        self.db.add(quiz)
        self.db.commit()
        return self._detail(self._get_quiz(quiz.id))

    def update_quiz(self, quiz_id: UUID, payload: QuizUpdate) -> AdminQuizDetail:
        quiz = self._get_quiz(quiz_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(quiz, field, value)
        self.db.commit()
        return self._detail(self._get_quiz(quiz.id))

    def delete_quiz(self, quiz_id: UUID) -> None:
        quiz = self._get_quiz(quiz_id)
        self.db.delete(quiz)
        self.db.commit()

    def add_question(self, quiz_id: UUID, payload: QuizQuestionCreate) -> AdminQuizDetail:
        quiz = self._get_quiz(quiz_id)
        if not any(option.is_correct for option in payload.options):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mark at least one option as correct",
            )
        order = payload.order_index or (len(quiz.questions) + 1)
        question = QuizQuestion(
            quiz_id=quiz.id,
            prompt=payload.prompt,
            explanation=payload.explanation,
            order_index=order,
        )
        self.db.add(question)
        self.db.flush()
        for index, option in enumerate(payload.options, start=1):
            self.db.add(
                QuizOption(
                    question_id=question.id,
                    label=option.label,
                    is_correct=option.is_correct,
                    order_index=index,
                )
            )
        self.db.commit()
        return self._detail(self._get_quiz(quiz.id))

    def update_question(self, question_id: UUID, payload: QuizQuestionUpdate) -> AdminQuizDetail:
        question = self._get_question(question_id)
        data = payload.model_dump(exclude_unset=True)
        if "prompt" in data:
            question.prompt = data["prompt"]
        if "explanation" in data:
            question.explanation = data["explanation"]
        if "order_index" in data and data["order_index"] is not None:
            question.order_index = data["order_index"]
        if "options" in data and data["options"] is not None:
            if not any(option.is_correct for option in data["options"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mark at least one option as correct",
                )
            for option in list(question.options):
                self.db.delete(option)
            self.db.flush()
            for index, option in enumerate(data["options"], start=1):
                self.db.add(
                    QuizOption(
                        question_id=question.id,
                        label=option.label,
                        is_correct=option.is_correct,
                        order_index=index,
                    )
                )
        self.db.commit()
        return self._detail(self._get_quiz(question.quiz_id))

    def delete_question(self, question_id: UUID) -> AdminQuizDetail:
        question = self._get_question(question_id)
        quiz_id = question.quiz_id
        self.db.delete(question)
        self.db.commit()
        return self._detail(self._get_quiz(quiz_id))
        return self._detail(self._get_quiz(quiz_id))