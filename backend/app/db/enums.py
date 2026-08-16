"""SQLAlchemy helpers so Postgres enums store Python Enum *values* (e.g. student), not names (STUDENT)."""

from enum import Enum as PyEnum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=PyEnum)


def pg_enum(enum_cls: type[E], *, name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        create_type=False,
        values_callable=lambda items: [item.value for item in items],
    )
