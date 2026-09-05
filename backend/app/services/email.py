"""Transactional email via Resend when EMAIL_API_KEY is set; otherwise log links (dev)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from html import escape
from urllib.parse import quote, urlencode

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_BASE = "https://api.resend.com"


def _resend_already_exists(status_code: int, body: str) -> bool:
    if status_code == 409:
        return True
    if status_code in {400, 422}:
        lowered = body.lower()
        return "already" in lowered or "exist" in lowered or "duplicate" in lowered
    return False


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_live(self) -> bool:
        return bool(self.settings.email_api_key)

    @property
    def newsletter_ready(self) -> bool:
        return bool(self.settings.email_api_key and self.settings.resend_audience_id)

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
                "You've been invited to manage Analytic Sages events, opportunities, and Insights publishing. "
                "Set your password to verify your email and open the operations dashboard."
            )
        elif role == "partnerships":
            subject = "You're invited to Analytic Sages grants & partnerships"
            title = "Grant manager invite"
            intro = (
                "You've been invited as a grants & partnerships manager. "
                "Set your password to verify your email and open the Opportunities Hub."
            )
        elif role == "editor":
            subject = "You're invited to edit Analytic Sages Insights"
            title = "Editor invite"
            intro = (
                "You've been invited as an Insights editor. "
                "Set your password to review author drafts and publish articles."
            )
        elif role == "author":
            subject = "You're invited to write for Analytic Sages Insights"
            title = "Author invite"
            intro = (
                "You've been invited as an Insights author. "
                "Set your password to write drafts and submit them for editorial review. "
                "Editors publish — authors cannot publish directly."
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

    def send_staff_promoted_email(
        self,
        *,
        email: str,
        full_name: str | None,
        role: str,
    ) -> None:
        login_link = f"{self.settings.frontend_url.rstrip('/')}/login"
        greeting = f"Hi {full_name}," if full_name else "Hi,"
        role_labels = {
            "operations": "operations manager",
            "partnerships": "grants & partnerships manager",
            "editor": "Insights editor",
            "author": "Insights author",
            "instructor": "instructor",
        }
        role_label = role_labels.get(role, "staff member")
        subject = f"Your Analytic Sages access is now {role_label}"
        html = self._simple_html(
            title="Staff access updated",
            body=(
                f"<p>{greeting}</p>"
                f"<p>Your Analytic Sages account is now set up as <strong>{role_label}</strong>. "
                "Sign in with your existing password to open the staff dashboard.</p>"
                f'<p><a href="{login_link}">Sign in</a></p>'
                f"<p style=\"color:#666;font-size:12px\">Or paste this link:<br>{login_link}</p>"
                "<p>If you were not expecting this, contact Analytic Sages support.</p>"
            ),
        )
        self._send(to=email, subject=subject, html=html, dev_label="staff-promoted", link=login_link)

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

    def add_subscriber(self, email: str) -> bool:
        """Add a guest email to the Insights Resend Audience / Segment. Idempotent."""
        address = email.strip().lower()
        if not self.newsletter_ready:
            if not self.settings.is_production:
                logger.info("[dev-email] insights-subscribe %s (list not configured)", address)
                return True
            logger.error("Insights subscribe failed: EMAIL_API_KEY or RESEND_AUDIENCE_ID missing")
            return False

        segment_id = self.settings.resend_audience_id
        created = self._resend(
            "POST",
            "/contacts",
            json={"email": address, "unsubscribed": False},
        )
        if created is None:
            return False
        status, body = created
        if status >= 400 and not _resend_already_exists(status, body):
            logger.error("Resend create contact failed status=%s body=%s", status, body[:400])
            return False

        encoded = quote(address, safe="")
        added = self._resend("POST", f"/contacts/{encoded}/segments/{segment_id}")
        if added is None:
            return False
        add_status, add_body = added
        if add_status >= 400 and not _resend_already_exists(add_status, add_body):
            logger.error(
                "Resend add contact to audience failed status=%s body=%s",
                add_status,
                add_body[:400],
            )
            return False

        self._resend("PATCH", f"/contacts/{encoded}", json={"unsubscribed": False})
        logger.info("Insights subscriber added: %s", address)
        return True

    def send_insight_newsletter(
        self,
        *,
        title: str,
        excerpt: str,
        byline: str,
        slug: str,
    ) -> bool:
        """Email the Insights list once per article. Custom mail stays in Resend Broadcasts."""
        url = f"{self.settings.frontend_url.rstrip('/')}/insights/{slug}"
        if not self.newsletter_ready:
            if self.settings.is_production:
                logger.error(
                    "Cannot send Insights newsletter for %s; EMAIL_API_KEY or RESEND_AUDIENCE_ID missing",
                    slug,
                )
                return False
            logger.info("[dev-email] insight-newsletter %s %s", title, url)
            return True

        html = self._insight_newsletter_html(
            title=title, excerpt=excerpt, byline=byline, url=url
        )
        created = self._resend(
            "POST",
            "/broadcasts",
            json={
                "segment_id": self.settings.resend_audience_id,
                "from": self.settings.email_from,
                "subject": title,
                "name": f"Insights · {slug}",
                "html": html,
                "send": True,
            },
        )
        if created is None:
            return False
        status, body = created
        if status >= 400:
            logger.error(
                "Resend insight broadcast failed status=%s body=%s slug=%s",
                status,
                body[:400],
                slug,
            )
            return False
        logger.info("Sent Insights newsletter for %s", slug)
        return True

    def send_opportunity_digest(
        self,
        *,
        counts: dict[str, int],
        listings: list[dict[str, str]],
        total: int,
    ) -> bool:
        hub = f"{self.settings.frontend_url.rstrip('/')}/opportunities"
        if not self.newsletter_ready:
            if self.settings.is_production:
                logger.error("Cannot send opportunities digest; EMAIL_API_KEY or RESEND_AUDIENCE_ID missing")
                return False
            logger.info("[dev-email] opportunities-digest total=%s counts=%s", total, counts)
            return True
        html = self._opportunity_digest_html(counts=counts, listings=listings, total=total, hub=hub)
        created = self._resend(
            "POST",
            "/broadcasts",
            json={
                "segment_id": self.settings.resend_audience_id,
                "from": self.settings.email_from,
                "subject": "Analytic Sages Opportunities Weekly",
                "name": f"Opportunities weekly · {datetime.now(UTC).date().isoformat()}",
                "html": html,
                "send": True,
            },
        )
        if created is None:
            return False
        status, body = created
        if status >= 400:
            logger.error("Resend opportunities digest failed status=%s body=%s", status, body[:400])
            return False
        logger.info("Sent opportunities weekly digest total=%s", total)
        return True

    def _opportunity_digest_html(
        self,
        *,
        counts: dict[str, int],
        listings: list[dict[str, str]],
        total: int,
        hub: str,
    ) -> str:
        labels = {
            "job": "Jobs",
            "internship": "Internships",
            "fellowship": "Fellowships",
            "hackathon": "Hackathons",
            "grant": "Grants",
            "bounty": "Bounties",
            "research": "Research",
        }
        summary = "".join(
            f'<li style="margin:0 0 6px">🔹 {counts[key]} {labels[key]}</li>'
            for key in labels
            if counts.get(key)
        ) or "<li>No new listings this week.</li>"
        items = "".join(
            f'<li style="margin:0 0 10px"><a href="{escape(item["url"])}">{escape(item["title"])}</a>'
            f' — {escape(item["organization_name"])}</li>'
            for item in listings
        )
        listing_html = f'<ul style="padding-left:18px;margin:0 0 24px">{items}</ul>' if items else ""
        return (
            '<div style="font-family:system-ui,-apple-system,sans-serif;line-height:1.5;'
            'max-width:560px;margin:0 auto;padding:24px;color:#0b1f33">'
            '<p style="margin:0 0 8px;font-size:12px;letter-spacing:0.04em;color:#c45c26;'
            'text-transform:uppercase">Analytic Sages Opportunities Weekly</p>'
            f'<h1 style="font-size:22px;line-height:1.3;margin:0 0 12px">This week\'s opportunities</h1>'
            f'<p style="margin:0 0 16px">{total} newly published, still-active listing'
            f'{"s" if total != 1 else ""}.</p>'
            f'<ul style="padding-left:18px;margin:0 0 20px">{summary}</ul>'
            f"{listing_html}"
            f'<p style="margin:0 0 24px"><a href="{escape(hub)}" '
            'style="display:inline-block;background:#0b1f33;color:#fff;text-decoration:none;'
            'padding:10px 16px;border-radius:8px">Explore all opportunities</a></p>'
            '<p style="margin:0;font-size:12px;color:#666">'
            '<a href="{{{RESEND_UNSUBSCRIBE_URL}}}" style="color:#666">Unsubscribe</a>'
            "</p>"
            "</div>"
        )

    def _insight_newsletter_html(
        self, *, title: str, excerpt: str, byline: str, url: str
    ) -> str:
        safe_title = escape(title)
        safe_excerpt = escape(excerpt) if excerpt else "A new Analytic Sages Insight is live."
        byline_html = (
            f'<p style="margin:0 0 16px;font-size:13px;color:#5a6a7a">By {escape(byline)}</p>'
            if byline
            else ""
        )
        return (
            '<div style="font-family:system-ui,-apple-system,sans-serif;line-height:1.5;'
            'max-width:560px;margin:0 auto;padding:24px;color:#0b1f33">'
            '<p style="margin:0 0 8px;font-size:12px;letter-spacing:0.04em;color:#c45c26;'
            'text-transform:uppercase">Analytic Sages Insights</p>'
            f'<h1 style="font-size:22px;line-height:1.3;margin:0 0 12px">{safe_title}</h1>'
            f"{byline_html}"
            f'<p style="margin:0 0 20px">{safe_excerpt}</p>'
            f'<p style="margin:0 0 24px"><a href="{escape(url)}" '
            'style="display:inline-block;background:#0b1f33;color:#fff;text-decoration:none;'
            'padding:10px 16px;border-radius:8px">Read the article</a></p>'
            '<p style="margin:0;font-size:12px;color:#666">'
            '<a href="{{{RESEND_UNSUBSCRIBE_URL}}}" style="color:#666">Unsubscribe</a>'
            "</p>"
            "</div>"
        )

    def _resend(
        self,
        method: str,
        path: str,
        json: dict[str, object] | None = None,
    ) -> tuple[int, str] | None:
        try:
            with httpx.Client(timeout=20.0) as client:
                kwargs: dict[str, object] = {
                    "headers": {
                        "Authorization": f"Bearer {self.settings.email_api_key}",
                        "Content-Type": "application/json",
                    },
                }
                if json is not None:
                    kwargs["json"] = json
                response = client.request(method, f"{RESEND_API_BASE}{path}", **kwargs)
        except httpx.HTTPError:
            logger.exception("Resend request failed %s %s", method, path)
            return None
        return response.status_code, response.text

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
