"""Quizzes: authoring, learner fetch, and server-side grading.

Answer keys never leave the server: the learner view strips ``is_correct`` and
grading happens here, so the browser can't read the correct option out of the API.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.payments import EnrollmentStatus
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.quiz import Quiz, QuizAnswer, QuizAttempt, QuizOption, QuizQuestion
from app.models.user import User
from app.schemas.quizzes import (
    QuizAttemptSummary,
    QuizOptionPublic,
    QuizPublic,
    QuizQuestionPublic,
    QuizQuestionResult,
    QuizResult,
)

STAFF_ROLES = {"admin", "instructor", "operations"}


class QuizService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------- helpers ----------

    def _quiz_query(self):
        return select(Quiz).options(
            selectinload(Quiz.questions).selectinload(QuizQuestion.options),
            selectinload(Quiz.course),
        )

    def _get_quiz(self, quiz_id: UUID) -> Quiz:
        quiz = self.db.scalar(self._quiz_query().where(Quiz.id == quiz_id))
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return quiz

    def _require_enrollment(self, user: User, course_id: UUID) -> Enrollment | None:
        enrollment = self.db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id,
                Enrollment.course_id == course_id,
                Enrollment.status.in_((EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED)),
            )
        )
        if enrollment:
            return enrollment
        # Staff can preview without an enrollment.
        if user.role.value in STAFF_ROLES:
            return None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enroll in this course to take its quizzes",
        )

    def _my_attempts(self, quiz_id: UUID, user_id: UUID) -> list[QuizAttempt]:
        return list(
            self.db.scalars(
                select(QuizAttempt).where(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.completed_at.is_not(None),
                )
            ).all()
        )

    @staticmethod
    def _summarize(quiz: Quiz, attempts: list[QuizAttempt]) -> QuizPublic:
        return QuizPublic(
            id=quiz.id,
            course_id=quiz.course_id,
            module_id=quiz.module_id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            description=quiz.description,
            pass_score=quiz.pass_score,
            order_index=quiz.order_index,
            questions_total=len(quiz.questions),
            best_score=max((a.score for a in attempts), default=None),
            passed=any(a.passed for a in attempts),
            attempts_count=len(attempts),
            last_attempt_at=max((a.completed_at for a in attempts), default=None),
        )

    # ---------- learner ----------

    def get_quiz_for_user(self, user: User, quiz_id: UUID) -> QuizPublic:
        quiz = self._get_quiz(quiz_id)
        self._require_enrollment(user, quiz.course_id)
        if not quiz.published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        attempts = self._my_attempts(quiz.id, user.id)
        summary = self._summarize(quiz, attempts)
        summary.questions = [
            QuizQuestionPublic(
                id=question.id,
                prompt=question.prompt,
                order_index=question.order_index,
                options=[
                    QuizOptionPublic(id=option.id, label=option.label)
                    for option in sorted(question.options, key=lambda o: o.order_index)
                ],
            )
            for question in sorted(quiz.questions, key=lambda q: q.order_index)
        ]
        return summary

    def submit_attempt(self, user: User, quiz_id: UUID, answers) -> QuizResult:
        quiz = self._get_quiz(quiz_id)
        enrollment = self._require_enrollment(user, quiz.course_id)
        if not quiz.questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="This quiz has no questions yet"
            )

        submitted = {str(a.question_id): a.option_id for a in answers}
        option_by_id: dict[str, QuizOption] = {}
        correct_by_question: dict[str, QuizOption | None] = {}
        for question in quiz.questions:
            for option in question.options:
                option_by_id[str(option.id)] = option
            correct_by_question[str(question.id)] = next(
                (o for o in question.options if o.is_correct), None
            )

        correct_count = 0
        results: list[QuizQuestionResult] = []
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user.id,
            enrollment_id=enrollment.id if enrollment else None,
            total_questions=len(quiz.questions),
            completed_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.flush()

        for question in sorted(quiz.questions, key=lambda q: q.order_index):
            selected_id = submitted.get(str(question.id))
            selected = option_by_id.get(str(selected_id)) if selected_id else None
            correct = correct_by_question[str(question.id)]
            is_correct = bool(selected and correct and selected.id == correct.id)
            if is_correct:
                correct_count += 1
            self.db.add(
                QuizAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    option_id=selected.id if selected else None,
                    is_correct=is_correct,
                )
            )
            results.append(
                QuizQuestionResult(
                    question_id=question.id,
                    prompt=question.prompt,
                    selected_option_id=selected.id if selected else None,
                    correct_option_id=correct.id if correct else None,
                    is_correct=is_correct,
                    explanation=question.explanation,
                )
            )

        total = len(quiz.questions)
        score = round((correct_count / total) * 100) if total else 0
        attempt.correct_count = correct_count
        attempt.score = score
        attempt.passed = score >= quiz.pass_score
        self.db.commit()
        self.db.refresh(attempt)

        return QuizResult(
            attempt_id=attempt.id,
            quiz_id=quiz.id,
            score=score,
            passed=attempt.passed,
            correct_count=correct_count,
            total_questions=total,
            pass_score=quiz.pass_score,
            completed_at=attempt.completed_at,
            results=results,
        )

    def list_my_attempts(self, user: User, quiz_id: UUID) -> list[QuizAttemptSummary]:
        quiz = self._get_quiz(quiz_id)
        self._require_enrollment(user, quiz.course_id)
        attempts = self._my_attempts(quiz.id, user.id)
        attempts.sort(key=lambda a: a.completed_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return [
            QuizAttemptSummary(
                id=a.id,
                quiz_id=a.quiz_id,
                score=a.score,
                passed=a.passed,
                correct_count=a.correct_count,
                total_questions=a.total_questions,
                completed_at=a.completed_at,
            )
            for a in attempts
        ]

    def list_quizzes_for_course(self, user: User, course_slug: str) -> list[QuizPublic]:
        course = self.db.scalar(select(Course).where(Course.slug == course_slug))
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        self._require_enrollment(user, course.id)
        quizzes = list(
            self.db.scalars(
                self._quiz_query()
                .where(Quiz.course_id == course.id, Quiz.published.is_(True))
                .order_by(Quiz.order_index)
            ).all()
        )
        return [
            self._summarize(quiz, self._my_attempts(quiz.id, user.id)) for quiz in quizzes
        ]