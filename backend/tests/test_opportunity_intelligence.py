from __future__ import annotations

from app.models.opportunity import OpportunitySourceTrustLevel, OpportunityType, WorkplaceType
from app.services.opportunity_normalize import (
    LocationScope,
    canonicalize_application_url,
    infer_workplace_and_scope,
    normalize_opportunity_fields,
)
from app.services.opportunity_relevance import score_relevance
from app.services.opportunity_sources.base import RawOpportunity


def test_canonicalize_strips_utm_and_slash():
    a = canonicalize_application_url("https://WWW.Example.com/jobs/1/?utm_source=x&utm_medium=y")
    b = canonicalize_application_url("https://example.com/jobs/1")
    assert a == b


def test_remote_us_only_not_worldwide():
    workplace, scope, country, region = infer_workplace_and_scope(
        location="Remote - US",
        title="Data Engineer",
        description="Remote US only",
    )
    assert workplace == WorkplaceType.REMOTE
    assert scope == LocationScope.US_ONLY
    assert country == "United States"


def test_remote_europe():
    workplace, scope, _, region = infer_workplace_and_scope(
        location="Remote - Europe",
        title="Analytics Engineer",
        description="",
    )
    assert workplace == WorkplaceType.REMOTE
    assert scope == LocationScope.EUROPE
    assert region == "europe"


def test_london_onsite_uk():
    workplace, scope, country, _ = infer_workplace_and_scope(
        location="London, UK",
        title="Research Analyst",
        description="Based in London",
    )
    assert workplace == WorkplaceType.ONSITE
    assert scope == LocationScope.UK_ONLY
    assert country == "United Kingdom"


def test_hybrid_detection():
    workplace, _, _, _ = infer_workplace_and_scope(
        location="Berlin",
        title="ML Engineer",
        description="Hybrid role with office days",
    )
    assert workplace == WorkplaceType.HYBRID


def test_normalize_preserves_location_raw():
    fields = normalize_opportunity_fields(
        title="  Senior Onchain Data Engineer ",
        organization_name="Example Protocol",
        description="SQL and Python",
        application_url="https://jobs.example.com/a?utm_campaign=x",
        source_url=None,
        location="Remote - US",
    )
    assert fields.location_raw == "Remote - US"
    assert "utm_campaign" not in fields.canonical_application_url
    assert fields.title == "Senior Onchain Data Engineer"


def test_high_relevance_data_engineer():
    raw = RawOpportunity(
        external_id="1",
        title="Blockchain Data Engineer",
        organization_name="Nansen",
        description="Build ETL pipelines with SQL, Python, Spark for onchain analytics.",
        location="Remote",
        application_url="https://jobs.example.com/1",
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.HIGH)
    assert float(result.score) >= 70
    assert result.match_reasons
    assert any("data" in r.lower() or "Exact" in r or "Skill" in r for r in result.match_reasons)


def test_high_relevance_quant():
    raw = RawOpportunity(
        external_id="2",
        title="Quantitative Researcher",
        organization_name="Fund",
        description="Systematic trading, market microstructure, Python statistics.",
        location="Remote - Europe",
        application_url="https://jobs.example.com/2",
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.HIGH)
    assert float(result.score) >= 60
    assert "quantitative-trading" in result.matched_career_tracks


def test_high_relevance_ai_agent():
    raw = RawOpportunity(
        external_id="3",
        title="AI Agent Engineer",
        organization_name="Lab",
        description="LangGraph multi-agent systems, tool calling, MCP.",
        location="Remote",
        application_url="https://jobs.example.com/3",
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.MEDIUM)
    assert float(result.score) >= 55
    assert "agentic-systems" in result.matched_career_tracks


def test_low_relevance_social_media():
    raw = RawOpportunity(
        external_id="4",
        title="Social Media Manager",
        organization_name="NFT Studio",
        description="Grow Discord and Twitter for our NFT brand.",
        location="Remote",
        application_url="https://jobs.example.com/4",
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.LOW)
    assert float(result.score) < 40


def test_low_relevance_nft_artist():
    raw = RawOpportunity(
        external_id="5",
        title="NFT Artist",
        organization_name="Studio",
        description="Create graphic designs for NFT collections.",
        location="Remote",
        application_url="https://jobs.example.com/5",
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.LOW)
    assert float(result.score) < 45


def test_ambiguous_security_researcher_not_blind_reject():
    raw = RawOpportunity(
        external_id="6",
        title="Security Researcher",
        organization_name="Protocol",
        description="Research protocol security and blockchain intelligence.",
        location="Remote",
        application_url="https://jobs.example.com/6",
        opportunity_type=OpportunityType.RESEARCH,
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.HIGH)
    # Ambiguous: may score mid-range, should not be forced to zero
    assert float(result.score) >= 15
