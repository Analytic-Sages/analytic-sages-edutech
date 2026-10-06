"""RealtimeKit recording-status webhook.

Cloudflare posts status changes here. A completed recording is archived to R2
with the same backfill used by the admin action. Other events are acknowledged
and not treated as a successful upload.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_recording_archive_service
from app.core.config import Settings, get_settings
from app.schemas.classroom_admin import RecordingArchiveResult
from app.services.recording_archive import RecordingArchiveService, verify_realtimekit_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _result(outcome) -> RecordingArchiveResult:
    return RecordingArchiveResult(
        recording_id=outcome.recording_id,
        success=outcome.success,
        outcome=outcome.outcome,
        detail=outcome.detail,
        bucket=outcome.bucket,
        object_key=outcome.object_key,
        size_bytes=outcome.size_bytes,
        provider_status=outcome.provider_status,
    )


@router.post("/realtimekit", response_model=RecordingArchiveResult)
async def realtimekit_recording_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    archive: RecordingArchiveService = Depends(get_recording_archive_service),
) -> RecordingArchiveResult:
    secret = settings.realtimekit_webhook_secret or ""
    body = await request.body()
    if not secret or not verify_realtimekit_signature(secret, body, dict(request.headers)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid RealtimeKit webhook signature",
        )
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RealtimeKit webhook body is not JSON",
        ) from None
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RealtimeKit webhook body is not an object",
        )
    outcome = archive.handle_webhook(payload)
    if outcome.retryable:
        logger.error(
            "RealtimeKit recording archive will be retried recording_id=%s outcome=%s",
            outcome.recording_id,
            outcome.outcome,
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=outcome.detail)
    return _result(outcome)
