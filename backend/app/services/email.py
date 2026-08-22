"""Transactional email via Resend when EMAIL_API_KEY is set; otherwise log links (dev)."""

from __future__ import annotations

import logging
from html import escape
from urllib.parse import urlencode

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_live(self) -> bool:
        return bool(self.settings.email_api_key)

    def send_verification_email(self, *, email: str, token: str, next_path: str | None = None) -> None:
        params = {"token": token}
        if next_path and next_path.startswith("/") and not next_path.startswith("//"):
            params["next"] = next_path
        link = f"{self.settings.frontend_url.rstrip('/')}/verify-email?{urlencode(params)}"
        subject = "Verify your Analytic Sages email"
        html = self._simple_html(
            title="Verify your email",
            body=(
                "<p>Welcome to Analytic Sages. Confirm your email to finish setting up "
                "your account.</p>"
                f'<p><a href="{link}">Verify email address</a></p>'
                f"<p style=\"color:#666;font-size:12px\">Or paste this link:<br>{link}</p>"
            ),
        )
        self._send(to=email, subject=subject, html=html, dev_label="verification", link=link)

    def send_password_reset_email(self, *, email: str, token: str) -> None:
        link = f"{self.settings.frontend_url.rstrip('/')}/reset-password?token={token}"
        subject = "Reset your Analytic Sages password"
        html = self._simple_html(
            title="Reset your password",
            body=(
                "<p>We received a request to reset your password.</p>"
                f'<p><a href="{link}">Choose a new password</a></p>'
                f"<p style=\"color:#666;font-size:12px\">Or paste this link:<br>{link}</p>"
                "<p>If you did not ask for this, you can ignore this email.</p>"
            ),
        )
        self._send(to=email, subject=subject, html=html, dev_label="password-reset", link=link)

    def send_staff_invite_email(
        self,
        *,
        email: str,
        token: str,
        full_name: str | None,
        role: str = "instructor",
    ) -> None:
        link = f"{self.settings.frontend_url.rstrip('/')}/staff-invite?token={token}"
        greeting = f"Hi {full_name}," if full_name else "Hi,"
        if role == "operations":
            subject = "You're invited to Analytic Sages operations"
            title = "Operations invite"
            intro = (
                "You've been invited to manage Analytic Sages events. "
                "Set your password to verify your email and open the events dashboard."
            )
        else:
            subject = "You're invited to Analytic Sages staff"
            title = "Staff invite"
            intro = (
                "You've been invited to join Analytic Sages as an instructor. "
                "Set your password to verify your email and open the staff classroom."
            )
        html = self._simple_html(
            title=title,
            body=(
                f"<p>{greeting}</p>"
                f"<p>{intro}</p>"
                f'<p><a href="{link}">Set your password and join</a></p>'
                f"<p style=\"color:#666;font-size:12px\">Or paste this link:<br>{link}</p>"
                "<p>This link expires in 7 days. If you were not expecting this, ignore the email.</p>"
            ),
        )
        self._send(to=email, subject=subject, html=html, dev_label="staff-invite", link=link)

    def send_payment_receipt(
        self,
        *,
        email: str,
        course_title: str,
        amount: int,
        currency: str,
        order_id: str,
        provider: str,
    ) -> None:
        if currency == "NGN":
            display_amount = f"₦{amount:,}"
        elif currency == "USD":
            display_amount = f"${amount:,}"
        else:
            display_amount = f"{currency} {amount}"

        subject = f"Payment receipt · {course_title}"
        html = self._simple_html(
            title="Payment received",
            body=(
                f"<p>Thanks for your payment for <strong>{course_title}</strong>.</p>"
                f"<p>Amount: {display_amount}<br>Order: {order_id}<br>Provider: {provider}</p>"
            ),
        )
        self._send(
            to=email,
            subject=subject,
            html=html,
            dev_label="receipt",
            link=f"order={order_id} amount={display_amount}",
        )

    def send_enrollment_confirmation(
        self,
        *,
        email: str,
        course_title: str,
        course_slug: str,
        access_path: str | None = None,
    ) -> None:
        path = access_path or f"/courses/{course_slug}"
        if not path.startswith("/"):
            path = f"/{path}"
        link = f"{self.settings.frontend_url.rstrip('/')}{path}"
        subject = f"You're in · {course_title}"
        html = self._simple_html(
            title="Enrollment confirmed",
            body=(
                f"<p>You now have access to <strong>{course_title}</strong>.</p>"
                f'<p><a href="{link}">Open your learning space</a></p>'
            ),
        )
        self._send(to=email, subject=subject, html=html, dev_label="enrollment", link=link)

    def send_contact_message(
        self,
        *,
        name: str,
        reply_email: str,
        subject: str,
        message: str,
    ) -> bool:
        if self.settings.is_production and not self.is_live:
            logger.error("Contact email skipped: EMAIL_API_KEY is not configured")
            return False
        inbox = self.settings.contact_email
        safe_name = escape(name)
        safe_email = escape(reply_email)
        safe_subject = escape(" ".join(subject.split()))
        safe_body = escape(message).replace("\n", "<br>")
        html = self._simple_html(
            title="Website contact",
            body=(
                f"<p><strong>From:</strong> {safe_name} &lt;{safe_email}&gt;</p>"
                f"<p><strong>Subject:</strong> {safe_subject}</p>"
                f"<p>{safe_body}</p>"
            ),
        )
        return self._send(
            to=inbox,
            subject=f"[Contact] {safe_subject}",
            html=html,
            dev_label="contact",
            link=f"from={reply_email} subject={subject}",
            reply_to=reply_email,
        )

    def send_event_registration_email(
        self,
        *,
        email: str,
        full_name: str | None,
        event_title: str,
        event_slug: str,
        starts_at,
        timezone_name: str,
    ) -> None:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        greeting = f"Hi {escape(full_name.split()[0])}," if full_name else "Hi,"
        link = f"{self.settings.frontend_url.rstrip('/')}/events/{event_slug}"
        try:
            zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            zone = None
        when = starts_at
        if getattr(starts_at, "tzinfo", None) and zone is not None:
            when = starts_at.astimezone(zone)
        when_label = when.strftime("%A, %d %B %Y · %H:%M")
        if timezone_name:
            when_label = f"{when_label} ({timezone_name})"
        html = self._simple_html(
            title="You're registered",
            body=(
                f"<p>{greeting}</p>"
                f"<p>You're registered for <strong>{escape(event_title)}</strong>.</p>"
                f"<p>{escape(when_label)}</p>"
                f'<p><a href="{link}">Open event page</a></p>'
                "<p>Use the same Analytic Sages account to join when the event goes live.</p>"
            ),
        )
        self._send(to=email, subject=f"You're registered · {event_title}", html=html, dev_label="event-rsvp", link=link)


    def _simple_html(self, *, title: str, body: str) -> str:
        return (
            '<div style="font-family:system-ui,-apple-system,sans-serif;line-height:1.5;'
            'max-width:560px;margin:0 auto;padding:24px;color:#0b1f33">'
            f"<h1 style=\"font-size:20px;margin:0 0 16px\">{title}</h1>"
            f"{body}"
            '<p style="margin-top:32px;font-size:12px;color:#666">Analytic Sages</p>'
            "</div>"
        )

    def _send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        dev_label: str,
        link: str,
        reply_to: str | None = None,
    ) -> bool:
        if not self.is_live:
            logger.info("[dev-email] %s for %s: %s", dev_label, to, link)
            return True

        payload: dict[str, object] = {
            "from": self.settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if reply_to:
            payload["reply_to"] = [reply_to]
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.settings.email_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError:
            logger.exception("Failed to send %s email to %s", dev_label, to)
            return False

        if response.status_code >= 400:
            logger.error(
                "Email provider error status=%s body=%s label=%s to=%s",
                response.status_code,
                response.text[:400],
                dev_label,
                to,
            )
            return False

        logger.info("Sent %s email to %s", dev_label, to)
        return True
