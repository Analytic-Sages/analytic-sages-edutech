"""Unit tests for hackathon date intelligence, classification, and relevance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.opportunity import HackathonEventFormat, OpportunitySourceTrustLevel, OpportunityType, WorkplaceType
from app.services.hackathon_dates import HackathonPhase, derive_hackathon_phase, registration_closes_in_days
from app.services.hackathon_normalize import event_format_from_workplace, normalize_hackathon_details, parse_prize
from app.services.hackathon_relevance import classify_event_type, score_hackathon_relevance
from app.services.opportunity_relevance import infer_opportunity_type, score_relevance
from app.services.opportunity_sources.base import RawOpportunity


def test_phase_open_when_registration_open():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    phase = derive_hackathon_phase(
        registration_deadline=now + timedelta(days=10),
        start_at=now + timedelta(days=14),
        end_at=now + timedelta(days=16),
        now=now,
    )
    assert phase == HackathonPhase.OPEN


def test_phase_ongoing_during_event():
    now = datetime(2026, 6, 15, tzinfo=UTC)
    phase = derive_hackathon_phase(
        registration_deadline=now - timedelta(days=2),
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=2),
        now=now,
    )
    assert phase == HackathonPhase.ONGOING


def test_phase_ended_after_end():
    now = datetime(2026, 6, 20, tzinfo=UTC)
    phase = derive_hackathon_phase(
        start_at=now - timedelta(days=5),
        end_at=now - timedelta(days=1),
        now=now,
    )
    assert phase == HackathonPhase.ENDED


def test_phase_upcoming_before_registration():
    now = datetime(2026, 5, 1, tzinfo=UTC)
    phase = derive_hackathon_phase(
        registration_open_at=now + timedelta(days=7),
        registration_deadline=now + timedelta(days=30),
        now=now,
    )
    assert phase == HackathonPhase.UPCOMING


def test_registration_closes_in_days():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    assert registration_closes_in_days(now + timedelta(days=3, hours=2), now=now) == 3


def test_event_format_from_workplace():
    assert event_format_from_workplace(WorkplaceType.REMOTE) == HackathonEventFormat.ONLINE
    assert event_format_from_workplace(WorkplaceType.HYBRID) == HackathonEventFormat.HYBRID
    assert (
        event_format_from_workplace(WorkplaceType.ONSITE, location="Berlin")
        == HackathonEventFormat.IN_PERSON
    )


def test_parse_prize_pool():
    amount, currency, raw = parse_prize("$50k USD")
    assert amount == Decimal("50000")
    assert currency == "USD"
    assert raw


def test_job_title_does_not_become_hackathon_from_description():
    raw = RawOpportunity(
        external_id="1",
        title="Senior Blockchain Data Engineer",
        organization_name="Acme",
        description="Join us. Prior hackathon experience preferred. Build data pipelines.",
        application_url="https://example.com/jobs/1",
    )
    assert infer_opportunity_type(raw) == OpportunityType.JOB
    assert classify_event_type(raw) == OpportunityType.JOB


def test_bounty_does_not_become_hackathon():
    raw = RawOpportunity(
        external_id="2",
        title="Protocol Bug Bounty",
        organization_name="Acme",
        description="Reward program for security researchers.",
        application_url="https://example.com/bounty",
        opportunity_type=OpportunityType.BOUNTY,
    )
    assert classify_event_type(raw) == OpportunityType.BOUNTY


def test_hackathon_title_classifies():
    raw = RawOpportunity(
        external_id="3",
        title="ETHGlobal Prague Hackathon",
        organization_name="ETHGlobal",
        description="Build on Ethereum.",
        application_url="https://ethglobal.com/events/prague",
        workplace_type=WorkplaceType.ONSITE,
    )
    assert infer_opportunity_type(raw) == OpportunityType.HACKATHON


def test_connector_hackathon_type_preserved():
    raw = RawOpportunity(
        external_id="4",
        title="Solana Breakpoint Build",
        organization_name="Colosseum",
        description="Solana builder competition with DeFi tracks.",
        application_url="https://colosseum.com/hackathon",
        opportunity_type=OpportunityType.HACKATHON,
        workplace_type=WorkplaceType.REMOTE,
        registration_deadline=datetime.now(UTC) + timedelta(days=14),
    )
    result = score_relevance(raw, OpportunitySourceTrustLevel.HIGH)
    assert result.opportunity_type == OpportunityType.HACKATHON
    assert result.score >= Decimal("60")


def test_normalize_hackathon_details_phase():
    now = datetime(2026, 6, 1, tzinfo=UTC)
    raw = RawOpportunity(
        external_id="5",
        title="Online DeFi Hackathon",
        organization_name="Devfolio",
        description="Build DeFi apps. Prize pool $25,000.",
        application_url="https://example.devfolio.co",
        workplace_type=WorkplaceType.REMOTE,
        opportunity_type=OpportunityType.HACKATHON,
        registration_deadline=now + timedelta(days=5),
        start_at=now + timedelta(days=7),
        end_at=now + timedelta(days=9),
        tags=["DeFi", "Solana"],
    )
    details = normalize_hackathon_details(raw, now=now)
    assert details.event_format == HackathonEventFormat.ONLINE
    assert details.derived_phase == HackathonPhase.OPEN.value
    assert details.prize_pool_amount == Decimal("25000")
    assert "DeFi" in details.tags


def test_hackathon_relevance_scores_focus():
    raw = RawOpportunity(
        external_id="6",
        title="AI Agents Hackathon",
        organization_name="Encode",
        description="Build autonomous onchain AI agents on Ethereum.",
        application_url="https://encode.club/hack",
        opportunity_type=OpportunityType.HACKATHON,
        workplace_type=WorkplaceType.REMOTE,
        deadline=datetime.now(UTC) + timedelta(days=10),
    )
    result = score_hackathon_relevance(raw, OpportunitySourceTrustLevel.HIGH)
    assert result.opportunity_type == OpportunityType.HACKATHON
    assert any("Focus:" in r or "Web3" in r for r in result.match_reasons)
