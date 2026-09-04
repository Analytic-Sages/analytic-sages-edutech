from __future__ import annotations

from app.services.opportunity_logos import resolve_organization_logo_url


def test_prefers_source_website_over_ats_application_url():
    url = resolve_organization_logo_url(
        source_website_url="https://phantom.com/jobs",
        application_url="https://boards.greenhouse.io/phantom/jobs/1",
    )
    assert url is not None
    assert "phantom.com" in url
    assert "greenhouse" not in url


def test_uses_application_host_when_not_ats():
    url = resolve_organization_logo_url(
        application_url="https://careers.nansen.ai/jobs/1",
    )
    assert url is not None
    assert "careers.nansen.ai" in url or "nansen.ai" in url


def test_skips_ats_only_urls():
    assert (
        resolve_organization_logo_url(
            application_url="https://boards.greenhouse.io/acme/jobs/1",
        )
        is None
    )


def test_explicit_wins():
    assert (
        resolve_organization_logo_url(
            explicit="https://cdn.example.com/logo.png",
            source_website_url="https://phantom.com",
        )
        == "https://cdn.example.com/logo.png"
    )
