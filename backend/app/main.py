from contextlib import asynccontextmanager, suppress
import asyncio
import logging
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import configure_logging, get_settings
from app.db.session import SessionLocal
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.email import EmailService
from app.services.payments import PaymentService
from app.services.seed_events import seed_featured_event
from app.services.seed_insights import seed_insights_articles
from app.services.seed_opportunities import seed_opportunity_taxonomy
from app.services.seed_self_paced import seed_dune_course

logger = logging.getLogger(__name__)


def _run_payments_reconcile_sweep() -> None:
    """Sync worker: pull real status for stale pending NOWPayments orders."""
    settings = get_settings()
    if not settings.nowpayments_api_key:
        return
    db = SessionLocal()
    try:
        service = PaymentService(db, settings, EmailService(settings))
        service.reconcile_stale_nowpayments(
            older_than_seconds=120,
            limit=settings.payments_reconcile_batch_limit,
        )
    except Exception:
        logger.exception("Payments reconcile sweep failed")
    finally:
        db.close()


async def _payments_reconcile_loop(stop: asyncio.Event) -> None:
    """Background self-heal for missed/late NOWPayments IPNs.

    Runs independently of the checkout tab, so a payment that settles after the
    student closed the page still unlocks their seat within one interval.
    """
    settings = get_settings()
    if not settings.payments_reconcile_enabled:
        return
    interval = max(60, settings.payments_reconcile_interval_seconds)

    # Let boot traffic and migrations settle before the first sweep.
    with suppress(asyncio.TimeoutError):
        await asyncio.wait_for(stop.wait(), timeout=30)

    while not stop.is_set():
        try:
            await asyncio.to_thread(_run_payments_reconcile_sweep)
        except Exception:
            logger.exception("Payments reconcile loop iteration failed")
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=interval)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        seed_dune_course(db)
        seed_featured_event(db)
        seed_insights_articles(db)
        seed_opportunity_taxonomy(db)
        db.commit()
        logger.info("Featured catalog content, Insights articles, and opportunity taxonomy are ready.")
    except Exception:
        db.rollback()
        logger.exception("Could not seed featured catalog content")
    finally:
        db.close()

    stop = asyncio.Event()
    reconcile_task = asyncio.create_task(_payments_reconcile_loop(stop))
    try:
        yield
    finally:
        stop.set()
        reconcile_task.cancel()
        with suppress(asyncio.CancelledError):
            await reconcile_task


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
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(api_router)

    redirect_host = urlparse(settings.resolved_google_redirect_uri).hostname
    frontend_host = urlparse(settings.frontend_url).hostname
    if settings.google_oauth_configured and redirect_host != frontend_host:
        logger.warning(
            "GOOGLE_REDIRECT_URI host %s does not match FRONTEND_URL host %s. "
            "Use the site origin so the refresh cookie is first-party.",
            redirect_host,
            frontend_host,
        )

    if settings.nowpayments_api_key:
        ipn_base = urlparse(settings.public_api_url)
        if ipn_base.hostname in {"localhost", "127.0.0.1"} or (
            settings.is_production and ipn_base.scheme != "https"
        ):
            logger.warning(
                "NOWPayments is live but PUBLIC_API_URL=%s is not a public HTTPS URL. "
                "IPN callbacks cannot arrive — payments will stay pending until reconciled.",
                settings.public_api_url,
            )
        if not settings.nowpayments_ipn_secret:
            logger.warning(
                "NOWPAYMENTS_API_KEY is set but NOWPAYMENTS_IPN_SECRET is empty — "
                "every IPN callback will be rejected and payments will not confirm automatically."
            )

    return app


app = create_app()
