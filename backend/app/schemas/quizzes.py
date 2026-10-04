from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------- learner-facing (never includes is_correct) ----------


class QuizOptionPublic(BaseModel):
    id: UUID
    label: str


class QuizQuestionPublic(BaseModel):
    id: UUID
    prompt: str
    order_index: int
    options: list[QuizOptionPublic] = Field(default_factory=list)


class QuizPublic(BaseModel):
    """A quiz the learner can take. Excludes answer keys."""

    id: UUID
    course_id: UUID
    module_id: UUID | None
    lesson_id: UUID | None
    title: str
    description: str
    pass_score: int
    order_index: int
    questions: list[QuizQuestionPublic] = Field(default_factory=list)
    questions_total: int = 0
    best_score: int | None = None
    passed: bool = False
    attempts_count: int = 0
    last_attempt_at: datetime | None = None


class QuizAnswerSubmit(BaseModel):
    question_id: UUID
    option_id: UUID | None = None


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerSubmit] = Field(default_factory=list)


class QuizQuestionResult(BaseModel):
    question_id: UUID
    prompt: str
    selected_option_id: UUID | None
    correct_option_id: UUID | None
    is_correct: bool
    explanation: str | None = None


class QuizResult(BaseModel):
    attempt_id: UUID
    quiz_id: UUID
    score: int
    passed: bool
    correct_count: int
    total_questions: int
    pass_score: int
    completed_at: datetime
    results: list[QuizQuestionResult] = Field(default_factory=list)


class QuizAttemptSummary(BaseModel):
    id: UUID
    quiz_id: UUID
    score: int
    passed: bool
    correct_count: int
    total_questions: int
    completed_at: datetime | None


# ---------- admin (full, includes answer keys) ----------


class AdminQuizOption(BaseModel):
    id: UUID
    label: str
    is_correct: bool
    order_index: int


class AdminQuizQuestion(BaseModel):
    id: UUID
    prompt: str
    explanation: str | None
    order_index: int
    options: list[AdminQuizOption] = Field(default_factory=list)


class AdminQuizRow(BaseModel):
    id: UUID
    course_id: UUID
    course_slug: str
    module_id: UUID | None
    lesson_id: UUID | None
    title: str
    description: str
    pass_score: int
    published: bool
    order_index: int
    questions_total: int
    attempts_count: int
    pass_rate: float


class AdminQuizDetail(AdminQuizRow):
    questions: list[AdminQuizQuestion] = Field(default_factory=list)


class QuizCreate(BaseModel):
    module_id: UUID | None = None
    lesson_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    pass_score: int = Field(default=70, ge=0, le=100)
    published: bool = True
    order_index: int | None = Field(default=None, ge=1)


class QuizUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    pass_score: int | None = Field(default=None, ge=0, le=100)
    published: bool | None = None
    order_index: int | None = Field(default=None, ge=1)


class QuizOptionInput(BaseModel):
    label: str = Field(min_length=1, max_length=1000)
    is_correct: bool = False


class QuizQuestionCreate(BaseModel):
    prompt: str = Field(min_length=1)
    explanation: str | None = None
    options: list[QuizOptionInput] = Field(min_length=2, max_length=8)
    order_index: int | None = Field(default=None, ge=1)


class QuizQuestionUpdate(BaseModel):
    prompt: str | None = Field(default=None, min_length=1)
    explanation: str | None = None
    options: list[QuizOptionInput] | None = Field(default=None, min_length=2, max_length=8)
    order_index: int | None = Field(default=None, ge=1)