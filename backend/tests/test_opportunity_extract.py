from __future__ import annotations

from app.models.opportunity import OpportunityType
from app.services.opportunity_extract import (
    is_incomplete_raw,
    merge_raw_with_extraction,
    validate_extraction_payload,
)
from app.services.opportunity_page_fetch import html_to_text
from app.services.opportunity_sources.base import RawOpportunity


def test_html_to_text_strips_scripts_and_tags():
    html = """
    <html><head><script>evil()</script><style>.x{}</style></head>
    <body><h1>Solana Builder Grant</h1><p>Apply by October.</p></body></html>
    """
    text = html_to_text(html)
    assert "Solana Builder Grant" in text
    assert "Apply by October" in text
    assert "evil" not in text
    assert "<h1>" not in text


def test_validate_extraction_keeps_nulls_and_rejects_junk_type():
    extracted = validate_extraction_payload(
        {
            "title": "Onchain Data Engineer",
            "organization_name": "Aave",
            "opportunity_type": "not-a-real-type",
            "description": None,
            "location": "Remote - Europe",
            "deadline": "2026-10-12",
            "skills": ["Python", "SQL", "", None],
            "compensation_text": "n/a",
            "confidence": 0.91,
        },
        provider="openai",
    )
    assert extracted.title == "Onchain Data Engineer"
    assert extracted.organization_name == "Aave"
    assert extracted.opportunity_type is None
    assert extracted.description is None
    assert extracted.location == "Remote - Europe"
    assert extracted.deadline is not None
    assert extracted.deadline.year == 2026
    assert extracted.skills == ["Python", "SQL"]
    assert extracted.compensation_text is None
    assert extracted.confidence == 0.91
    assert "opportunity_type" not in extracted.fields_filled
    assert "title" in extracted.fields_filled


def test_validate_extraction_accepts_percent_confidence():
    extracted = validate_extraction_payload({"confidence": 85, "title": "Grant"})
    assert extracted.confidence == 0.85
    assert extracted.title == "Grant"


def test_is_incomplete_raw_detects_thin_description():
    thin = RawOpportunity(
        external_id="1",
        title="Data Engineer",
        organization_name="Protocol",
        description="Short",
        application_url="https://example.com/jobs/1",
    )
    rich = RawOpportunity(
        external_id="2",
        title="Data Engineer",
        organization_name="Protocol",
        description="x" * 300,
        application_url="https://example.com/jobs/2",
    )
    assert is_incomplete_raw(thin) is True
    assert is_incomplete_raw(rich) is False


def test_merge_raw_fills_only_thin_fields():
    raw = RawOpportunity(
        external_id="1",
        title="Data Engineer",
        organization_name="Protocol",
        description="Short blurb",
        location="",
        application_url="https://example.com/jobs/1",
        opportunity_type=OpportunityType.JOB,
    )
    extracted = validate_extraction_payload(
        {
            "title": "Senior Onchain Data Engineer",
            "organization_name": "Protocol Labs",
            "description": "Build pipelines for blockchain data with Python and SQL." * 5,
            "location": "Remote - Worldwide",
            "opportunity_type": "job",
            "skills": ["Python", "SQL"],
            "confidence": 0.9,
        }
    )
    merged = merge_raw_with_extraction(raw, extracted)
    assert merged.title == "Data Engineer"  # existing title kept
    assert merged.organization_name == "Protocol"  # existing org kept
    assert "blockchain data" in merged.description
    assert merged.location == "Remote - Worldwide"
    assert "Python" in merged.tags
    assert merged.raw_data.get("ai_extraction", {}).get("confidence") == 0.9


def test_merge_raw_skips_low_confidence():
    raw = RawOpportunity(
        external_id="1",
        title="Data Engineer",
        organization_name="Protocol",
        description="Short",
        application_url="https://example.com/jobs/1",
    )
    extracted = validate_extraction_payload(
        {
            "description": "Invented long description that should not apply because confidence is low." * 3,
            "confidence": 0.2,
        }
    )
    merged = merge_raw_with_extraction(raw, extracted)
    assert merged.description == "Short"
