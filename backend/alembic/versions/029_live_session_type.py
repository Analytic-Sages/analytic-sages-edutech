"""Add live session type (teaching vs office hour).

Revision ID: 029_live_session_type
Revises: 028_insight_contributors
Create Date: 2026-10-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "029_live_session_type"
down_revision: Union[str, None] = "028_insight_contributors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE live_session_type AS ENUM ('teaching', 'office_hour')")
    session_type = postgresql.ENUM(
        "teaching", "office_hour", name="live_session_type", create_type=False
    )
    op.add_column(
        "live_sessions",
        sa.Column(
            "session_type",
            session_type,
            nullable=False,
            server_default="teaching",
        ),
    )


def downgrade() -> None:
    op.drop_column("live_sessions", "session_type")
    op.execute("DROP TYPE live_session_type")