from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import configure_logging, get_settings
from app.db.session import SessionLocal
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.seed_events import seed_featured_event
from app.services.seed_self_paced import seed_dune_course

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        seed_dune_course(db)
        seed_featured_event(db)
        db.commit()
        logger.info("Featured self-paced course and event are ready.")
    except Exception:
        db.rollback()
        logger.exception("Could not seed featured catalog content")
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="Analytic Sages API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(api_router)
    return app


app = create_app()
