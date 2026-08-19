from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_email_service, get_rate_limiter
from app.core.rate_limit import enforce_rate_limit
from app.schemas.auth import MessageResponse
from app.schemas.contact import ContactRequest
from app.services.email import EmailService

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", response_model=MessageResponse)
def submit_contact(
    request: Request,
    payload: ContactRequest,
    email_service: EmailService = Depends(get_email_service),
    rate_limiter=Depends(get_rate_limiter),
) -> MessageResponse:
    enforce_rate_limit(rate_limiter, request, scope="contact")
    sent = email_service.send_contact_message(
        name=payload.name.strip(),
        reply_email=str(payload.email),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
    )
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "We could not send your message right now. "
                "Please email support@analyticsages.io instead."
            ),
        )
    return MessageResponse(message="Message sent. We will reply to the email you provided.")
