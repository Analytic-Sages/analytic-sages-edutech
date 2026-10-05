from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AtRiskStudentRow(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None = None
    missed_sessions: int = 0
    missing_assignments: int = 0
    incomplete_projects: int = 0
    at_risk: bool = False


class CohortReport(BaseModel):
    cohort_id: UUID
    cohort_name: str
    student_count: int = 0
    attendance_rate: int = 0
    assignment_completion_rate: int = 0
    projects_completed: int = 0
    at_risk_count: int = 0
    at_risk: list[AtRiskStudentRow] = Field(default_factory=list)
