from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CertificateEligibilityPublic(BaseModel):
    cohort_id: UUID
    cohort_name: str
    programme_slug: str | None = None
    programme_title: str | None = None
    eligible: bool = False
    attendance_percent: int = 0
    assignments_submitted: int = 0
    assignments_total: int = 0
    projects_completed: int = 0
    requirements: dict[str, Any] = Field(default_factory=dict)
