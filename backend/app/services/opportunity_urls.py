from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from fastapi import HTTPException, status

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}
SHORT_LINK_HOSTS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "ow.ly",
    "goo.gl",
    "is.gd",
    "buff.ly",
    "rebrand.ly",
    "cutt.ly",
    "shorturl.at",
}

# Job aggregators and boards we refuse to import from, even if a model suggests them.
AGGREGATOR_HOSTS = {
    "linkedin.com",
    "www.linkedin.com",
    "indeed.com",
    "www.indeed.com",
    "glassdoor.com",
    "www.glassdoor.com",
    "wellfound.com",
    "angel.co",
    "www.angel.co",
    "web3.career",
    "www.web3.career",
    "crypto.jobs",
    "web3.jobs",
    "www.web3.jobs",
    "remoteok.com",
    "www.remoteok.com",
    "levellabs.com",
    "www.levellabs.com",
    "otta.com",
    "www.otta.com",
}


def validate_http_url(url: str, field: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} must be an http or https URL",
        )
    host = parsed.hostname or ""
    if host.lower() in BLOCKED_HOSTS or host.endswith(".localhost"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} host is not allowed",
        )
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field} host is not allowed",
            )
    except ValueError:
        pass
    return url.strip()


def is_allowed_fetch_url(url: str) -> bool:
    try:
        validate_http_url(url, "url")
        return True
    except HTTPException:
        return False


def hostname_of(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).hostname
    return host.lower() if host else None


def is_aggregator_url(url: str) -> bool:
    host = hostname_of(url)
    if not host:
        return False
    if host in AGGREGATOR_HOSTS:
        return True
    return any(host.endswith(f".{item}") for item in AGGREGATOR_HOSTS if not item.startswith("www."))


def is_shortened_url(url: str) -> bool:
    host = hostname_of(url)
    if not host:
        return False
    return host in SHORT_LINK_HOSTS or host.endswith(".bit.ly")
