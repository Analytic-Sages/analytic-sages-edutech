"""Unit tests for bounty date intelligence, classification, and relevance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.opportunity import BountyCategory, OpportunitySourceTrustLevel, OpportunityType, WorkplaceType
from app.services.bounty_dates import BountyPhase, closes_in_days, derive_bounty_phase
from app.services.bounty_normalize import infer_bounty_category, normalize_bounty_details, parse_reward
from app.services.bounty_relevance import classify_bounty_type, score_bounty_relevance
from app.services.opportunity_relevance import infer_opportunity_type, score_relevance
from app.services.opportunity_sources.base import RawOpportunity


def test_phase_open():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    assert (
        derive_bounty_phase(deadline=now + timedelta(days=20), now=now) == BountyPhase.OPEN
    )


def test_phase_closing_soon():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    assert (
        derive_bounty_phase(deadline=now + timedelta(days=3), now=now)
        == BountyPhase.CLOSING_SOON
    )


def test_phase_ended_after_deadline():
    now = datetime(2026, 6, 10, tzinfo=UTC)
    assert (
        derive_bounty_phase(deadline=now - timedelta(days=1), now=now) == BountyPhase.ENDED
    )


def test_phase_ended_when_winners_announced():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    assert (
        derive_bounty_phase(
            deadline=now + timedelta(days=10),
            winners_announced=True,
            now=now,
        )
        == BountyPhase.ENDED
    )


def test_closes_in_days():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    assert closes_in_days(now + timedelta(days=2, hours=5), now=now) == 2


def test_parse_reward():
    amount, token, raw = parse_reward("Reward 500 USDC")
    assert amount == Decimal("500")
    assert token == "USDC"
    assert raw


def test_infer_bug_bounty_category():
    assert infer_bounty_category("Protocol Bug Bounty", "Report vulns") == BountyCategory.BUG


def test_infer_content_category():
    assert infer_bounty_category("Write a Twitter thread", "content bounty") == BountyCategory.CONTENT


def test_job_does_not_become_bounty():
    raw = RawOpportunity(
        external_id="1",
        title="Senior Security Engineer",
        organization_name="Acme",
        description="Bug bounty experience preferred.",
        application_url="https://example.com/jobs/1",
    )
    assert infer_opportunity_type(raw) == OpportunityType.JOB
    assert classify_bounty_type(raw) == OpportunityType.JOB


def test_hackathon_does_not_become_bounty():
    raw = RawOpportunity(
        external_id="2",
        title="ETHGlobal Hackathon",
        organization_name="ETHGlobal",
        description="Earn prizes",
        application_url="https://ethglobal.com/x",
        opportunity_type=OpportunityType.HACKATHON,
    )
    assert classify_bounty_type(raw) == OpportunityType.HACKATHON


def test_bounty_title_classifies():
    raw = RawOpportunity(
        external_id="3",
        title="Solana Content Bounty",
        organization_name="Superteam",
        description="Write about Solana DeFi.",
        application_url="https://superteam.fun/earn/listing/x",
    )
    assert infer_opportunity_type(raw) == OpportunityType.BOUNTY


def test_score_bounty_relevance():
    raw = RawOpportunity(
        external_id="4",
        title="DeFi Bug Bounty",
        organization_name="Protocol",
        description="Security researchers earn USDC for Ethereum smart contract findings.",
        application_url="https://immunefi.com/x",
        opportunity_type=OpportunityType.BOUNTY,
        workplace_type=WorkplaceType.REMOTE,
        reward_amount=Decimal("10000"),
        reward_token="USDC",
        deadline=datetime.now(UTC) + timedelta(days=14),
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.HIGH)
    assert result.opportunity_type == OpportunityType.BOUNTY
    assert result.score >= Decimal("60")


def test_normalize_bounty_details():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    raw = RawOpportunity(
        external_id="5",
        title="Nigeria Content Bounty",
        organization_name="Superteam NG",
        description="Reward 250 USDC for Solana content.",
        application_url="https://superteam.fun/earn/listing/nigeria-content-bounty",
        opportunity_type=OpportunityType.BOUNTY,
        reward_amount=Decimal("250"),
        reward_token="USDC",
        bounty_deadline=now + timedelta(days=5),
        winners_announced=False,
        bounty_skills=["writing", "solana"],
    )
    details = normalize_bounty_details(raw, now=now)
    assert details.reward_amount == Decimal("250")
    assert details.reward_token == "USDC"
    assert details.derived_phase == BountyPhase.CLOSING_SOON.value
    assert details.category in {BountyCategory.CONTENT, BountyCategory.OTHER, BountyCategory.DEVELOPMENT}
    assert "writing" in details.skills


def test_score_bounty_rejects_job_shaped():
    raw = RawOpportunity(
        external_id="6",
        title="Senior Backend Engineer",
        organization_name="Acme",
        description="Work on bounty platform",
        application_url="https://example.com/jobs/2",
        opportunity_type=OpportunityType.BOUNTY,
    )
    result = score_bounty_relevance(raw, OpportunitySourceTrustLevel.MEDIUM)
    assert result.opportunity_type == OpportunityType.JOB
