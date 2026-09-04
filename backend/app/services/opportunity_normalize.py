from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.models.opportunity import EmploymentType, LocationScope, WorkplaceType

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "campaign",
}


@dataclass
class NormalizedOpportunityFields:
    title: str
    organization_name: str
    description: str
    application_url: str
    canonical_application_url: str
    source_url: str | None
    location_raw: str
    location: str
    country: str | None
    region: str | None
    location_scope: LocationScope
    workplace_type: WorkplaceType
    employment_type: EmploymentType | None


def clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def canonicalize_application_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "https").lower()
    netloc = (parsed.netloc or "").lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = re.sub(r"/{2,}", "/", parsed.path or "")
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_organization(name: str) -> str:
    cleaned = clean_whitespace(name)
    # Drop trailing Inc/LLC noise for soft matching only at call sites; keep display form.
    return cleaned


def infer_employment_type(text: str) -> EmploymentType | None:
    blob = text.lower()
    if re.search(r"\b(intern|internship)\b", blob):
        return EmploymentType.INTERNSHIP
    if re.search(r"\b(part[\s-]?time)\b", blob):
        return EmploymentType.PART_TIME
    if re.search(r"\b(contract|contractor|freelance)\b", blob):
        return EmploymentType.CONTRACT
    if re.search(r"\b(volunteer)\b", blob):
        return EmploymentType.VOLUNTEER
    if re.search(r"\b(full[\s-]?time|permanent)\b", blob):
        return EmploymentType.FULL_TIME
    return None


def infer_workplace_and_scope(
    *,
    location: str,
    title: str = "",
    description: str = "",
    explicit_workplace: WorkplaceType | None = None,
) -> tuple[WorkplaceType, LocationScope, str | None, str | None]:
    """Never invent REMOTE WORLDWIDE unless the source text supports it."""
    loc = clean_whitespace(location)
    blob = f"{title} {loc} {description}".lower()

    workplace = explicit_workplace
    if workplace is None:
        if re.search(r"\bhybrid\b", blob):
            workplace = WorkplaceType.HYBRID
        elif re.search(r"\b(onsite|on-site|in[\s-]?office)\b", blob):
            workplace = WorkplaceType.ONSITE
        elif re.search(r"\bremote\b", blob) or not loc:
            workplace = WorkplaceType.REMOTE
        else:
            workplace = WorkplaceType.ONSITE

    country: str | None = None
    region: str | None = None
    scope = LocationScope.UNKNOWN

    # Explicit remote geo constraints first.
    if re.search(r"\bremote\b.*\b(us only|usa only|united states only|us-only)\b", blob) or re.search(
        r"\b(us only|usa only|united states only)\b", blob
    ):
        scope = LocationScope.US_ONLY
        country = "United States"
        region = "north_america"
    elif re.search(r"\bremote\b.*\b(uk only|united kingdom only)\b", blob) or re.search(
        r"\b(uk only|united kingdom only)\b", blob
    ):
        scope = LocationScope.UK_ONLY
        country = "United Kingdom"
        region = "europe"
    elif re.search(r"\bremote\b.*\beurope\b", blob) or re.search(r"\beurope only\b", blob):
        scope = LocationScope.EUROPE
        region = "europe"
    elif re.search(r"\bremote\b.*\bemea\b", blob) or "emea" in blob:
        scope = LocationScope.EMEA
        region = "europe"
    elif re.search(r"\b(worldwide|anywhere in the world|work from anywhere)\b", blob):
        # Only worldwide when explicitly stated.
        scope = LocationScope.WORLDWIDE
        region = "global"
    elif re.search(r"\b(global|anywhere)\b", blob) and "remote" in blob and "us" not in blob:
        # "Remote - Anywhere" without worldwide → global remote, not worldwide claim.
        scope = LocationScope.GLOBAL
        region = "global"
    elif any(token in blob for token in ("nigeria", "lagos", "abuja")):
        scope = LocationScope.AFRICA
        country = "Nigeria"
        region = "nigeria"
    elif any(token in blob for token in ("africa", "kenya", "ghana", "rwanda")):
        scope = LocationScope.AFRICA
        region = "africa"
    elif any(token in blob for token in ("london", "berlin", "amsterdam", "paris", "lisbon", "europe")):
        scope = LocationScope.EUROPE
        region = "europe"
        if "london" in blob or "uk" in blob or "united kingdom" in blob:
            country = "United Kingdom"
            if "remote" not in blob:
                scope = LocationScope.UK_ONLY
    elif any(
        token in blob
        for token in ("united states", "usa", "new york", "san francisco", "canada", "north america")
    ):
        scope = LocationScope.NORTH_AMERICA
        region = "north_america"
        if "canada" in blob:
            country = "Canada"
        elif any(t in blob for t in ("united states", "usa", "new york", "san francisco")):
            country = "United States"
            if "remote" in blob:
                scope = LocationScope.US_ONLY
    elif loc:
        scope = LocationScope.OTHER
        region = "global"
    else:
        scope = LocationScope.UNKNOWN
        region = "remote" if workplace == WorkplaceType.REMOTE else None

    return workplace, scope, country, region


def normalize_opportunity_fields(
    *,
    title: str,
    organization_name: str,
    description: str,
    application_url: str,
    source_url: str | None,
    location: str,
    workplace_type: WorkplaceType | None = None,
    employment_type: EmploymentType | None = None,
) -> NormalizedOpportunityFields:
    title_clean = clean_whitespace(title)[:255]
    org_clean = clean_whitespace(organization_name)[:255]
    desc_clean = (description or "").strip()
    app_url = (application_url or "").strip()
    loc_raw = clean_whitespace(location)[:255]
    workplace, scope, country, region = infer_workplace_and_scope(
        location=loc_raw,
        title=title_clean,
        description=desc_clean,
        explicit_workplace=workplace_type,
    )
    employment = employment_type or infer_employment_type(
        f"{title_clean} {loc_raw} {desc_clean[:2000]}"
    )
    return NormalizedOpportunityFields(
        title=title_clean,
        organization_name=org_clean,
        description=desc_clean,
        application_url=app_url,
        canonical_application_url=canonicalize_application_url(app_url),
        source_url=(source_url.strip() if source_url else None),
        location_raw=loc_raw,
        location=loc_raw or (
            "Remote"
            if workplace == WorkplaceType.REMOTE
            else ""
        ),
        country=country,
        region=region,
        location_scope=scope,
        workplace_type=workplace,
        employment_type=employment,
    )
