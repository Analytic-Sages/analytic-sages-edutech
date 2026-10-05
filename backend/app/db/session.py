from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# psycopg2 has no default connect timeout, so a dead/unreachable database would
# block forever instead of failing. Bound the handshake so callers (and tests)
# surface a clear OperationalError instead of hanging.
_connect_args: dict[str, object] = {}
if str(settings.database_url).startswith("postgresql"):
    _connect_args["connect_timeout"] = settings.database_connect_timeout_seconds

engine = create_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
