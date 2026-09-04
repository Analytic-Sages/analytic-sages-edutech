"""Resolve organization logo URLs for opportunity cards."""

from __future__ import annotations

from urllib.parse import urlparse

# ATS / aggregator hosts where a favicon is the board, not the employer.
ATS_OR_PLATFORM_HOSTS = {
    "boards.greenhouse.io",
    "boards-api.greenhouse.io",
    "job-boards.greenhouse.io",
    "greenhouse.io",
    "jobs.lever.co",
    "api.lever.co",
    "lever.co",
    "jobs.ashbyhq.com",
    "api.ashbyhq.com",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "workday.com",
    "linkedin.com",
    "www.linkedin.com",
    "indeed.com",
    "www.indeed.com",
    "wellfound.com",
    "angel.co",
    "www.angel.co",
}


def hostname_of(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = (urlparse(url.strip()).hostname or "").lower()
    except Exception:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def is_employer_host(host: str | None) -> bool:
    if not host:
        return False
    if host in ATS_OR_PLATFORM_HOSTS:
        return False
    # Subdomains of ATS platforms (e.g. company.wd1.myworkdayjobs.com)
    for blocked in ATS_OR_PLATFORM_HOSTS:
        if host == blocked or host.endswith("." + blocked):
            return False
    return True


def favicon_logo_url(host: str) -> str:
    """Stable, keyless logo proxy sized for list/detail cards."""
    return f"https://www.google.com/s2/favicons?domain={host}&sz=128"


def resolve_organization_logo_url(
    *,
    explicit: str | None = None,
    source_website_url: str | None = None,
    application_url: str | None = None,
    source_url: str | None = None,
) -> str | None:
    """Pick the best logo URL. Prefer explicit, then company site, then apply URL."""
    if explicit and explicit.strip():
        return explicit.strip()[:500]
    for candidate in (source_website_url, source_url, application_url):
        host = hostname_of(candidate)
        if is_employer_host(host):
            assert host is not None
            return favicon_logo_url(host)[:500]
    return None
