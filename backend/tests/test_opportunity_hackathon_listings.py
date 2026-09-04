from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.core.roles import UserRole
from app.models.opportunity import OpportunitySource
from app.services.opportunity_sources.colosseum import parse_listing as parse_colosseum
from app.services.opportunity_sources.devfolio import parse_listing as parse_devfolio
from app.services.opportunity_sources.devpost import parse_listing as parse_devpost
from app.services.opportunity_sources.dorahacks import parse_listing as parse_dorahacks
from app.services.opportunity_sources.encode import parse_listing as parse_encode
from app.services.opportunity_sources.superteam import parse_listing as parse_superteam
from app.services.opportunity_sources.web3_filter import is_web3_text
from tests.test_opportunity_ingestion import _auth, _cleanup_source, _cleanup_user, _make_user, _seed, client

COLOSSEUM_PAYLOAD = {
    "type": "data",
    "nodes": [
        {"type": "data", "data": [{"session": 1}, "ignore"]},
        {
            "type": "data",
            "data": [
                {"currentEvent": 1},
                {
                    "eventType": 2,
                    "name": 3,
                    "phase": 4,
                    "landingPageUrl": 5,
                    "description": 6,
                    "countdownTarget": 7,
                    "programs": 8,
                    "ctaText": 9,
                },
                "eternal",
                "Eternal Challenge 2026 H2",
                "open",
                "https://colosseum.com/eternal",
                "Start building now.",
                "2026-09-07T00:00:00.000Z",
                {"hackathon": 10, "eternal": 14},
                "Start Building",
                {"name": 11, "active": 12, "phase": 13, "landingPageUrl": 15},
                "Frontier",
                False,
                "concluded",
                {"active": 16, "label": 17, "landingPageUrl": 5},
                "https://colosseum.com/frontier",
                True,
                "Open",
            ],
        },
    ],
}

DEVPOST_HTML = """
<html><body>
<h2>Our current online Blockchain hackathons</h2>
<article class="hackathon-tile ">
  <a class="clearfix" href="https://3rd-web-hack.devpost.com/">
    <h5 class="title">3rd-Web-Hack</h5>
    <p class="challenge-description">Build solutions to existing Blockchain problems</p>
    <p class="challenge-location"><i></i> Online</p>
  </a>
</article>
<article class="hackathon-tile ">
  <a href="https://help.devpost.com/">
    <h5 class="title">Help Center</h5>
  </a>
</article>
<h2>Our current in-person Blockchain hackathons</h2>
<article class="hackathon-tile ">
  <a href="https://compsphere12.devpost.com/">
    <h5 class="title">COMPSPHERE 12</h5>
    <p class="challenge-description">Campus blockchain build</p>
    <p class="challenge-location">Eldoret, Kenya</p>
  </a>
</article>
<h2>Top Blockchain builders of 2026</h2>
<article class="hackathon-tile ">
  <a href="https://old-chain.devpost.com/">
    <h5 class="title">Old Chain Hack</h5>
    <p class="challenge-description">Past event</p>
  </a>
</article>
<h2>Recent Blockchain hackathons</h2>
<article class="hackathon-tile ">
  <a href="https://recent-chain.devpost.com/">
    <h5 class="title">Recent Chain</h5>
  </a>
</article>
</body></html>
"""

DEVFOLIO_PAYLOAD = {
    "result": [
        {
            "name": "MUBA Blockchain Hackathon",
            "slug": "muba-blockchain",
            "tagline": "Build onchain",
            "desc": "A blockchain hackathon",
            "is_online": True,
            "themes": [{"name": "Blockchain"}],
            "hackathon_setting": {"subdomain": "muba-blockchain", "reg_ends_at": "2026-09-01T00:00:00.000Z"},
        },
        {
            "name": "Recursion Edition II",
            "slug": "recursion-edition",
            "tagline": "THE LOOP IS BACK",
            "desc": "24-hour offline hackathon for healthtech and climate",
            "is_online": False,
            "city": "Chennai",
            "country": "India",
            "themes": [{"name": "No Restrictions"}],
            "hackathon_setting": {"subdomain": "recursion-edition"},
        },
    ]
}

DORAHACKS_HTML = """
<html><body>
<script type="application/json">
[["Reactive",1],{"path":2},"/hackathon?status=upcoming","/hackathon/weex-ai-wars2/","/hackathon/buidl-ctc-2026-fall/"]
</script>
</body></html>
"""


def test_web3_filter_requires_blockchain_terms():
    assert is_web3_text("AI x Blockchain Global Hackathon")
    assert is_web3_text("zero knowledge proofs")
    assert not is_web3_text("Healthtech climate hackathon")


def test_colosseum_parser_keeps_open_challenge_not_concluded():
    source = OpportunitySource(name="Colosseum", connector_type="colosseum", config={})
    items = parse_colosseum(COLOSSEUM_PAYLOAD, source)
    assert [item.external_id for item in items] == ["eternal"]
    assert items[0].title == "Eternal Challenge 2026 H2"
    assert items[0].application_url == "https://colosseum.com/eternal"
    assert items[0].opportunity_type.value == "hackathon"
    assert items[0].raw_data["event_type"] == "eternal"


def test_devpost_parser_keeps_current_blockchain_tiles_only():
    source = OpportunitySource(name="Devpost", connector_type="devpost", config={})
    items = parse_devpost(DEVPOST_HTML, source)
    slugs = [item.external_id for item in items]
    assert slugs == ["3rd-web-hack", "compsphere12"]
    assert items[0].application_url == "https://3rd-web-hack.devpost.com/"
    assert items[0].workplace_type.value == "remote"
    assert items[1].workplace_type.value == "onsite"
    assert "old-chain" not in slugs
    assert "help" not in slugs


def test_devfolio_parser_applies_web3_filter():
    source = OpportunitySource(name="Devfolio", connector_type="devfolio", config={})
    items = parse_devfolio(DEVFOLIO_PAYLOAD, source)
    assert [item.external_id for item in items] == ["muba-blockchain"]
    assert items[0].application_url == "https://muba-blockchain.devfolio.co"
    assert items[0].opportunity_type.value == "hackathon"


def test_dorahacks_parser_reads_listing_slugs():
    source = OpportunitySource(name="DoraHacks", connector_type="dorahacks", config={})
    items = parse_dorahacks(DORAHACKS_HTML, source)
    assert [item.external_id for item in items] == ["weex-ai-wars2", "buidl-ctc-2026-fall"]
    assert items[0].application_url == "https://dorahacks.io/hackathon/weex-ai-wars2"
    assert all(item.opportunity_type.value == "hackathon" for item in items)


def test_encode_parser_keeps_upcoming_hackathons_only():
    source = OpportunitySource(name="Encode Club", connector_type="encode", config={})
    now = datetime(2026, 8, 28, tzinfo=UTC)
    items = parse_encode(
        [
            {
                "encode_id": "E1001",
                "official_name": "Encode Web3 AI Hackathon",
                "type": "Hackathon",
                "start_date": "1 September 2026",
                "end_date": "30 September 2026",
                "website_url": "https://www.encode.club/web3-ai-hackathon",
            },
            {
                "encode_id": "E0661",
                "official_name": "Etherlink Hackathon 2025",
                "type": "Hackathon",
                "start_date": "9 July 2025",
                "end_date": "5 August 2025",
                "website_url": "https://etherlink.encode.club/",
            },
            {
                "encode_id": "E2000",
                "official_name": "Encode Solidity Bootcamp",
                "type": "Bootcamp",
                "start_date": "1 September 2026",
                "end_date": "30 September 2026",
                "website_url": "https://www.encode.club/bootcamp",
            },
        ],
        source,
        now=now,
    )
    assert [item.external_id for item in items] == ["E1001"]
    assert items[0].opportunity_type.value == "hackathon"


def test_superteam_parser_splits_hackathon_bounty_and_grant():
    source = OpportunitySource(name="Superteam Earn", connector_type="superteam", config={})
    items = parse_superteam(
        [
            {
                "id": "1",
                "type": "bounty",
                "status": "OPEN",
                "title": "Create Content for Breakpoint 2026",
                "slug": "create-content-for-breakpoint-2026",
                "rewardAmount": 8000,
                "token": "USDG",
                "deadline": "2026-09-07T21:59:59.999Z",
                "isWinnersAnnounced": False,
                "sponsor": {"name": "Superteam Germany"},
            },
            {
                "id": "2",
                "type": "hackathon",
                "status": "OPEN",
                "title": "Radar Demo Day Nigeria",
                "slug": "radar-demo-day-nigeria",
                "sponsor": {"name": "Superteam Nigeria"},
            },
            {
                "id": "3",
                "type": "project",
                "status": "OPEN",
                "title": "Solana Summit Creator Grant",
                "slug": "solana-summit-creator-grant",
                "sponsor": {"name": "Superteam Singapore"},
            },
            {
                "id": "4",
                "type": "job",
                "status": "OPEN",
                "title": "Protocol Engineer",
                "slug": "protocol-engineer",
            },
        ],
        source,
    )
    by_slug = {item.external_id: item for item in items}
    assert set(by_slug) == {"1", "2", "3"}
    assert by_slug["1"].opportunity_type.value == "bounty"
    assert by_slug["2"].opportunity_type.value == "hackathon"
    assert by_slug["2"].application_url == "https://superteam.fun/earn/listing/radar-demo-day-nigeria"
    assert by_slug["3"].opportunity_type.value == "grant"


def test_colosseum_ingest_lands_as_draft_hackathon():
    _seed()
    source_name = f"Col {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-col-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "website_url": "https://colosseum.com/hackathon",
                "connector_type": "colosseum",
                "trust_level": "high",
                "auto_publish_allowed": False,
                "config": {},
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["config"]["listing_url"] == "https://colosseum.com/hackathon/__data.json"
        source = OpportunitySource(name="Colosseum", connector_type="colosseum", config={})
        items = parse_colosseum(COLOSSEUM_PAYLOAD, source)
        connector = MagicMock()
        connector.fetch.return_value = items
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(
                f"/api/v1/admin/opportunity-sources/{created.json()['id']}/sync",
                headers=_auth(admin),
            )
        assert synced.status_code == 200, synced.text
        assert synced.json()["created"] == 1
        listed = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"q": "Eternal Challenge"})
        match = next(item for item in listed.json()["items"] if item["title"] == "Eternal Challenge 2026 H2")
        assert match["status"] == "draft"
        assert match["opportunity_type"] == "hackathon"
        assert match["application_url"] == "https://colosseum.com/eternal"
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_superteam_ingest_keeps_bounty_type():
    _seed()
    source_name = f"ST {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-st-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "website_url": "https://superteam.fun/earn",
                "connector_type": "superteam",
                "trust_level": "high",
                "auto_publish_allowed": False,
                "config": {},
            },
        )
        assert created.status_code == 201, created.text
        source = OpportunitySource(name="Superteam Earn", connector_type="superteam", config={})
        items = parse_superteam(
            [
                {
                    "id": "b1",
                    "type": "bounty",
                    "status": "OPEN",
                    "title": "Nigeria Content Bounty",
                    "slug": "nigeria-content-bounty",
                    "sponsor": {"name": "Superteam Nigeria"},
                }
            ],
            source,
        )
        connector = MagicMock()
        connector.fetch.return_value = items
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(
                f"/api/v1/admin/opportunity-sources/{created.json()['id']}/sync",
                headers=_auth(admin),
            )
        assert synced.status_code == 200, synced.text
        listed = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"q": "Nigeria Content Bounty"})
        match = next(item for item in listed.json()["items"] if item["title"] == "Nigeria Content Bounty")
        assert match["status"] == "draft"
        assert match["opportunity_type"] == "bounty"
        assert match["application_url"] == "https://superteam.fun/earn/listing/nigeria-content-bounty"
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)
