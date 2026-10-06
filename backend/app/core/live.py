from enum import Enum


class ProgrammeStatus(str, Enum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CohortEnrollmentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    SUSPENDED = "suspended"


class AttendanceStatus(str, Enum):
    ATTENDED = "attended"
    LATE = "late"
    ABSENT = "absent"
    # Imported from a provider (e.g. RealtimeKit) but not confidently matched to an
    # enrolled student — an instructor must resolve it before it counts.
    NEEDS_REVIEW = "needs_review"


class AttendanceSyncStatus(str, Enum):
    """State of the provider↔LMS attendance reconciliation for a session/row."""

    OK = "ok"
    # The session is still running (or the provider has not published data yet).
    PENDING = "pending"
    # Imported, but something needs a human: unmatched participant(s).
    NEEDS_REVIEW = "needs_review"
    # The provider call failed; safe to retry.
    ERROR = "error"


class AssignmentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"
    RETURNED = "returned"
    LATE = "late"
    MISSING = "missing"


class ProjectStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    COMPLETED = "completed"
