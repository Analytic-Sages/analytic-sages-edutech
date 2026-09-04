from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.opportunity import (
    Opportunity,
    OpportunityIngestion,
    OpportunitySource,
    OpportunitySyncRun,
)
from app.models.user import User
from app.services.opportunity_mission import is_off_mission_title
from app.services.opportunity_sources.base import RawOpportunity
from app.services.opportunity_sources.ashby import parse_jobs as parse_ashby_jobs
from app.services.opportunity_sources.greenhouse import parse_jobs
from app.services.opportunity_sources.lever import parse_jobs as parse_lever_jobs
from app.services.opportunity_sources.ethglobal import parse_listing
from app.services.opportunity_sources.rss import parse_feed
from app.services.seed_opportunities import seed_opportunity_taxonomy

client = TestClient(app)

RELEVANT_DESCRIPTION = (
    "We need an onchain data engineer for blockchain analytics, crypto data, and web3 protocol research. "
    "You will write SQL and Python, build ETL pipelines, use Dune, and support quantitative forensics "
    "and agentic DeFi investigations."
)


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(user_id=str(user.id), role=user.role.value)


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(email: str, role: UserRole) -> User:
    db = SessionLocal()
    try:
        user = User(email=email, full_name=email.split("@")[0], role=role, email_verified=True, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _cleanup_user(email: str) -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def _cleanup_source(name: str) -> None:
    db = SessionLocal()
    try:
        source = db.scalar(select(OpportunitySource).where(OpportunitySource.name == name))
        if not source:
            return
        for run in db.scalars(select(OpportunitySyncRun).where(OpportunitySyncRun.source_id == source.id)).all():
            db.delete(run)
        for ingestion in db.scalars(
            select(OpportunityIngestion).where(OpportunityIngestion.source_id == source.id)
        ).all():
            db.delete(ingestion)
        opps = db.scalars(select(Opportunity).where(Opportunity.source_id == source.id)).all()
        for opp in opps:
            db.delete(opp)
        db.delete(source)
        db.commit()
    finally:
        db.close()


def _seed() -> None:
    db = SessionLocal()
    try:
        seed_opportunity_taxonomy(db)
        db.commit()
    finally:
        db.close()


def test_greenhouse_parser_extracts_jobs_without_http():
    source = OpportunitySource(
        name="Greenhouse Co",
        connector_type="greenhouse",
        config={"board_token": "example"},
    )
    items = parse_jobs(
        {
            "jobs": [
                {
                    "id": 99,
                    "title": "Blockchain Data Engineer",
                    "absolute_url": "https://boards.greenhouse.io/example/jobs/99",
                    "location": {"name": "Remote"},
                    "content": "<p>SQL and Python onchain analytics.</p>",
                    "updated_at": "2026-08-01T00:00:00Z",
                }
            ]
        },
        source,
    )
    assert len(items) == 1
    assert items[0].external_id == "99"
    assert items[0].application_url.endswith("/99")
    assert "SQL" in items[0].description


def test_lever_parser_extracts_jobs_without_http():
    source = OpportunitySource(name="Lever Co", connector_type="lever", config={"board_token": "example"})
    items = parse_lever_jobs(
        [
            {
                "id": "lev-1",
                "text": "Onchain Data Analyst",
                "hostedUrl": "https://jobs.lever.co/example/lev-1",
                "categories": {"location": "Remote"},
                "workplaceType": "remote",
                "descriptionPlain": "SQL pipelines for blockchain analytics.",
                "createdAt": 1750000000000,
            }
        ],
        source,
    )
    assert len(items) == 1
    assert items[0].external_id == "lev-1"
    assert items[0].application_url.endswith("/lev-1")
    assert "SQL" in items[0].description


def test_ashby_parser_extracts_jobs_without_http():
    source = OpportunitySource(name="Dune", connector_type="ashby", config={"board_token": "dune"})
    items = parse_ashby_jobs(
        {
            "jobs": [
                {
                    "id": "abc",
                    "title": "Software Engineer",
                    "isListed": True,
                    "location": "Remote",
                    "isRemote": True,
                    "workplaceType": "Remote",
                    "jobUrl": "https://jobs.ashbyhq.com/dune/abc",
                    "descriptionPlain": "Build pipelines that ingest onchain blockchain data with SQL.",
                    "department": "Engineering",
                    "publishedAt": "2026-07-20T07:00:48.904+00:00",
                }
            ]
        },
        source,
    )
    assert len(items) == 1
    assert items[0].external_id == "abc"
    assert items[0].application_url.endswith("/abc")
    assert "onchain" in items[0].description.lower()


def test_ashby_ranks_engineering_ahead_of_sales():
    source = OpportunitySource(name="TRM Labs", connector_type="ashby", config={"board_token": "trm-labs"})
    items = parse_ashby_jobs(
        {
            "jobs": [
                {
                    "id": "sales",
                    "title": "Account Director, Defence and Intel",
                    "isListed": True,
                    "jobUrl": "https://jobs.ashbyhq.com/trm-labs/sales",
                    "department": "Go-To-Market",
                    "descriptionPlain": "Enterprise sales.",
                },
                {
                    "id": "eng",
                    "title": "Senior Data Engineer",
                    "isListed": True,
                    "jobUrl": "https://jobs.ashbyhq.com/trm-labs/eng",
                    "department": "R&D",
                    "descriptionPlain": "Onchain graph analytics.",
                },
            ]
        },
        source,
    )
    assert [item.external_id for item in items] == ["eng", "sales"]


ETHGLOBAL_LISTING_HTML = """
<html><body>
<h2>Featured 3</h2>
<a href="/events/tokyo2026">
  <div class="uppercase text-xs font-semibold tracking-wider">September</div>
  <span class="">25</span><span class="">27</span>
  <h2>ETHGlobal Tokyo 2026</h2>
  <span class="">Tokyo<!-- -->, <!-- -->Japan</span>
  <span class="">IRL Hackathon</span>
</a>
<a href="/events/ethconf2027">
  <h2>ETHConf 2027</h2>
  <span class="">Conference</span>
</a>
<h2>Upcoming 8</h2>
<a href="/events/ethonline2026">
  <div class="uppercase text-xs font-semibold tracking-wider">September</div>
  <span class="">4</span><span class="">16</span>
  <h2>ETHOnline 2026</h2>
  <span class="">Online</span>
  <span class="">Async Hackathon</span>
</a>
<a href="/events/happy-hour-tokyo">
  <h2>ETHGlobal Happy Hour Tokyo</h2>
  <span class="">Meetup</span>
</a>
<a href="/events/tokyo2026">
  <h2>ETHGlobal Tokyo 2026</h2>
  <span class="">IRL Hackathon</span>
</a>
<a href="/events/cannes">
  <h2>ETHGlobal Cannes 2026</h2>
  <span class="">Hackathon</span>
</a>
<h2>Past 323</h2>
<a href="/events/lisbon">
  <h2>ETHGlobal Lisbon 2026</h2>
  <span class="">Hackathon</span>
</a>
</body></html>
"""


def test_ethglobal_parser_keeps_upcoming_hackathons_only():
    source = OpportunitySource(name="ETHGlobal", connector_type="ethglobal", config={})
    items = parse_listing(ETHGLOBAL_LISTING_HTML, source)
    slugs = [item.external_id for item in items]
    assert slugs == ["tokyo2026", "ethonline2026", "cannes"]
    assert all(item.opportunity_type.value == "hackathon" for item in items)
    tokyo = items[0]
    assert tokyo.title == "ETHGlobal Tokyo 2026"
    assert tokyo.application_url == "https://ethglobal.com/events/tokyo2026"
    assert tokyo.location == "Tokyo, Japan"
    assert tokyo.workplace_type.value == "onsite"
    assert tokyo.raw_data["ethglobal_type"] == "IRL Hackathon"
    assert items[1].workplace_type.value == "remote"
    assert items[1].location == "Online"
    assert "lisbon" not in slugs
    assert "ethconf2027" not in slugs
    assert "happy-hour-tokyo" not in slugs


def test_ethglobal_ingest_lands_as_draft_hackathon():
    _seed()
    source_name = f"ETHG {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-ethg-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "website_url": "https://ethglobal.com/events",
                "connector_type": "ethglobal",
                "trust_level": "high",
                "auto_publish_allowed": False,
                "config": {},
            },
        )
        assert created.status_code == 201, created.text
        source_id = created.json()["id"]
        assert created.json()["config"]["events_url"] == "https://ethglobal.com/events"
        source = OpportunitySource(name="ETHGlobal", connector_type="ethglobal", config={})
        items = parse_listing(ETHGLOBAL_LISTING_HTML, source)
        connector = MagicMock()
        connector.fetch.return_value = items
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.status_code == 200, synced.text
        assert synced.json()["status"] == "completed"
        assert synced.json()["created"] == 3
        listed = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"q": "ETHGlobal Tokyo"})
        match = next(item for item in listed.json()["items"] if item["title"] == "ETHGlobal Tokyo 2026")
        assert match["status"] == "draft"
        assert match["opportunity_type"] == "hackathon"
        assert match["application_url"] == "https://ethglobal.com/events/tokyo2026"
        assert match["is_manual"] is False
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_recruiter_title_is_off_mission_even_with_intelligence():
    assert is_off_mission_title("Senior Technical Recruiter – Cybersecurity & Threat Intelligence")
    assert is_off_mission_title("Account Director, Defence and Intel")
    assert not is_off_mission_title("Senior Blockchain Intelligence Analyst")


def test_official_sources_are_seeded():
    _seed()
    admin_email = f"admin-src-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        listed = client.get("/api/v1/admin/opportunity-sources", headers=_auth(admin))
        assert listed.status_code == 200, listed.text
        items = listed.json()["items"]
        by_name = {item["name"]: item for item in items}
        assert "Nansen" in by_name
        assert by_name["Nansen"]["connector_type"] == "greenhouse"
        assert by_name["Nansen"]["config"]["board_token"] == "nansen"
        assert by_name["Nansen"]["auto_publish_allowed"] is False
        assert "Dune" in by_name
        assert by_name["Dune"]["connector_type"] == "ashby"
        assert by_name["Dune"]["config"]["board_token"] == "dune"
        assert "TRM Labs" in by_name
        assert by_name["TRM Labs"]["config"]["board_token"] == "trm-labs"
        assert "Consensys" in by_name
        assert by_name["Consensys"]["connector_type"] == "greenhouse"
        assert "OpenZeppelin" in by_name
        assert "Phantom" in by_name
        assert by_name["Phantom"]["connector_type"] == "ashby"
        assert "ETHGlobal" in by_name
        assert by_name["ETHGlobal"]["connector_type"] == "ethglobal"
        assert by_name["ETHGlobal"]["auto_publish_allowed"] is False
        assert by_name["ETHGlobal"]["config"]["events_url"] == "https://ethglobal.com/events"
        assert by_name["Colosseum"]["connector_type"] == "colosseum"
        assert by_name["Devpost Blockchain"]["connector_type"] == "devpost"
        assert by_name["Devfolio"]["connector_type"] == "devfolio"
        assert by_name["DoraHacks"]["connector_type"] == "dorahacks"
        assert by_name["Encode Club"]["connector_type"] == "encode"
        assert by_name["Superteam Earn"]["connector_type"] == "superteam"
        assert by_name["Superteam Earn"]["auto_publish_allowed"] is False
        assert by_name["Superteam Earn"]["config"]["listing_url"] == "https://superteam.fun/api/listings"
    finally:
        _cleanup_user(admin_email)


def test_rss_parser_extracts_items_without_http():
    xml = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>Onchain Data Analyst</title>
          <link>https://example.com/jobs/onchain</link>
          <guid>job-1</guid>
          <description>Work with blockchain analytics and SQL.</description>
        </item>
      </channel>
    </rss>
    """
    source = OpportunitySource(name="Parser Source", connector_type="rss", config={"feed_url": "https://example.com/feed"})
    items = parse_feed(xml, source)
    assert len(items) == 1
    assert items[0].title == "Onchain Data Analyst"
    assert items[0].external_id == "job-1"
    assert items[0].application_url == "https://example.com/jobs/onchain"


def test_rss_ingest_lands_as_draft_review_required():
    _seed()
    source_name = f"RSS {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-ing-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "trust_level": "medium",
                "auto_publish_allowed": False,
                "config": {"feed_url": "https://example.com/jobs.xml"},
            },
        )
        assert created.status_code == 201, created.text
        source_id = created.json()["id"]
        raw = RawOpportunity(
            external_id="ext-1",
            title="Onchain Data Analyst",
            organization_name=source_name,
            description=RELEVANT_DESCRIPTION,
            application_url=f"https://example.com/careers/onchain-analyst-{uuid.uuid4().hex[:8]}",
        )
        connector = MagicMock()
        connector.fetch.return_value = [raw]
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.status_code == 200, synced.text
        body = synced.json()
        assert body["status"] == "completed"
        assert body["created"] == 1
        review = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"review": True})
        assert review.status_code == 200
        match = next(item for item in review.json()["items"] if item["title"] == "Onchain Data Analyst")
        assert match["status"] == "draft"
        assert match["trust_status"] == "review_required"
        assert match["is_manual"] is False
        assert match["relevance_score"] is not None
        public = client.get("/api/v1/opportunities")
        assert all(item["id"] != match["id"] for item in public.json()["items"])
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_admin_sync_all_sources_lands_as_draft():
    _seed()
    source_name = f"RSS all {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-sync-all-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    apply_url = f"https://example.com/careers/sync-all-{uuid.uuid4().hex[:8]}"
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "trust_level": "medium",
                "auto_publish_allowed": False,
                "config": {"feed_url": "https://example.com/jobs.xml"},
            },
        )
        assert created.status_code == 201, created.text
        source_id = created.json()["id"]
        raw = RawOpportunity(
            external_id="ext-all-1",
            title="Onchain Data Analyst",
            organization_name=source_name,
            description=RELEVANT_DESCRIPTION,
            application_url=apply_url,
        )

        def connector_for(source):
            mock = MagicMock()
            mock.fetch.return_value = [raw] if str(source.id) == source_id else []
            return mock

        with patch("app.services.opportunity_ingestion.get_connector", side_effect=connector_for):
            synced = client.post("/api/v1/admin/opportunities/sync-sources", headers=_auth(admin))
        assert synced.status_code == 200, synced.text
        body = synced.json()
        assert body["published"] is False
        assert body["created"] >= 1
        assert any(run["source_id"] == source_id and run["created"] == 1 for run in body["runs"])
        review = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"review": True})
        match = next(item for item in review.json()["items"] if item["application_url"] == apply_url)
        assert match["status"] == "draft"
        assert match["trust_status"] == "review_required"
        public = client.get("/api/v1/opportunities")
        assert all(item["id"] != match["id"] for item in public.json()["items"])
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_exact_url_is_confirmed_duplicate():
    _seed()
    source_name = f"RSS {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-dup-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    url = f"https://example.com/careers/{uuid.uuid4().hex[:8]}"
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "config": {"feed_url": "https://example.com/feed.xml"},
            },
        )
        source_id = created.json()["id"]
        first = RawOpportunity(
            external_id="a",
            title="Onchain Data Analyst",
            organization_name=source_name,
            description=RELEVANT_DESCRIPTION,
            application_url=url,
        )
        second = RawOpportunity(
            external_id="b",
            title="Different Title Entirely",
            organization_name=source_name,
            description=RELEVANT_DESCRIPTION,
            application_url=url,
        )
        connector = MagicMock()
        connector.fetch.return_value = [first, second]
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.status_code == 200, synced.text
        assert synced.json()["created"] == 1
        assert synced.json()["duplicates"] == 1
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_low_relevance_is_rejected_and_kept():
    _seed()
    source_name = f"RSS {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-low-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "config": {"feed_url": "https://example.com/feed.xml"},
            },
        )
        source_id = created.json()["id"]
        raw = RawOpportunity(
            external_id="camp-1",
            title="Hotel receptionist",
            organization_name=source_name,
            description="Greet guests at the front desk and manage room keys.",
            application_url=f"https://example.com/jobs/receptionist-{uuid.uuid4().hex[:8]}",
        )
        connector = MagicMock()
        connector.fetch.return_value = [raw]
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.json()["rejected"] == 1
        listed = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"status": "rejected"})
        match = next(item for item in listed.json()["items"] if item["title"] == "Hotel receptionist")
        assert match["status"] == "rejected"
        public = client.get("/api/v1/opportunities")
        assert all(item["id"] != match["id"] for item in public.json()["items"])
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_high_risk_does_not_auto_publish():
    _seed()
    source_name = f"RSS {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-risk-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "trust_level": "high",
                "auto_publish_allowed": True,
                "config": {"feed_url": "https://example.com/feed.xml"},
            },
        )
        source_id = created.json()["id"]
        raw = RawOpportunity(
            external_id="risk-1",
            title="Onchain Data Engineer",
            organization_name=source_name,
            description=f"{RELEVANT_DESCRIPTION} Applicants must pay to apply and send crypto today.",
            application_url=f"https://example.com/jobs/onchain-engineer-{uuid.uuid4().hex[:8]}",
        )
        connector = MagicMock()
        connector.fetch.return_value = [raw]
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.json()["created"] == 1
        listed = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"review": True})
        match = next(item for item in listed.json()["items"] if item["external_id"] == "risk-1")
        assert match["status"] == "draft"
        assert match["trust_status"] == "high_risk"
        assert any(flag["flag_type"] == "PAY_TO_APPLY" for flag in match["risk_flags"])
        public = client.get("/api/v1/opportunities")
        assert all(item["id"] != match["id"] for item in public.json()["items"])
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_never_auto_publishes_even_when_flag_set():
    """Trust-first: external ingest always enters review, never public publish."""
    _seed()
    source_name = f"RSS {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-auto-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "trust_level": "high",
                "auto_publish_allowed": True,
                "config": {"feed_url": "https://example.com/feed.xml"},
            },
        )
        assert created.json()["auto_publish_allowed"] is False
        source_id = created.json()["id"]
        raw = RawOpportunity(
            external_id="auto-1",
            title="Onchain Data Engineer",
            organization_name=source_name,
            description=RELEVANT_DESCRIPTION,
            application_url=f"https://example.com/jobs/onchain-data-engineer-{uuid.uuid4().hex[:8]}",
        )
        connector = MagicMock()
        connector.fetch.return_value = [raw]
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.json()["created"] == 1
        listed = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"review": True})
        match = next(item for item in listed.json()["items"] if item["external_id"] == "auto-1")
        assert match["status"] == "draft"
        assert match["trust_status"] in {"review_required", "high_risk"}
        assert match.get("match_reasons") is not None
        public = client.get("/api/v1/opportunities")
        assert all(item["id"] != match["id"] for item in public.json()["items"])
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_off_mission_title_is_rejected():
    _seed()
    source_name = f"RSS {uuid.uuid4().hex[:8]}"
    admin_email = f"admin-off-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(admin),
            json={
                "name": source_name,
                "connector_type": "rss",
                "config": {"feed_url": "https://example.com/feed.xml"},
            },
        )
        source_id = created.json()["id"]
        raw = RawOpportunity(
            external_id="sales-1",
            title="Account Executive",
            organization_name=source_name,
            description=RELEVANT_DESCRIPTION,
            application_url=f"https://example.com/jobs/ae-{uuid.uuid4().hex[:8]}",
        )
        connector = MagicMock()
        connector.fetch.return_value = [raw]
        with patch("app.services.opportunity_ingestion.get_connector", return_value=connector):
            synced = client.post(f"/api/v1/admin/opportunity-sources/{source_id}/sync", headers=_auth(admin))
        assert synced.json()["rejected"] == 1
        review = client.get("/api/v1/admin/opportunities", headers=_auth(admin), params={"review": True})
        assert all(item["external_id"] != "sales-1" for item in review.json()["items"])
    finally:
        _cleanup_source(source_name)
        _cleanup_user(admin_email)


def test_non_admin_cannot_manage_sources_or_sync():
    _seed()
    author_email = f"author-ing-{uuid.uuid4()}@example.com"
    ops_email = f"ops-ing-{uuid.uuid4()}@example.com"
    author = _make_user(author_email, UserRole.AUTHOR)
    ops = _make_user(ops_email, UserRole.OPERATIONS)
    blocked_payload = {
        "name": f"Blocked {uuid.uuid4().hex[:8]}",
        "connector_type": "rss",
        "config": {"feed_url": "https://example.com/feed.xml"},
    }
    ops_payload = {
        "name": f"Ops Source {uuid.uuid4().hex[:8]}",
        "connector_type": "rss",
        "config": {"feed_url": "https://example.com/ops-feed.xml"},
    }
    try:
        # Authors cannot manage opportunity sources / sync
        assert (
            client.post(
                "/api/v1/admin/opportunity-sources",
                headers=_auth(author),
                json=blocked_payload,
            ).status_code
            == 403
        )
        assert client.get("/api/v1/admin/opportunity-sources", headers=_auth(author)).status_code == 403
        assert (
            client.get(
                "/api/v1/admin/opportunities", headers=_auth(author), params={"review": True}
            ).status_code
            == 403
        )
        assert (
            client.post("/api/v1/admin/opportunities/sync-sources", headers=_auth(author)).status_code
            == 403
        )
        # Operations may manage opportunity ops surfaces
        created = client.post(
            "/api/v1/admin/opportunity-sources",
            headers=_auth(ops),
            json=ops_payload,
        )
        assert created.status_code == 201
        assert client.get("/api/v1/admin/opportunity-sources", headers=_auth(ops)).status_code == 200
        assert (
            client.get(
                "/api/v1/admin/opportunities", headers=_auth(ops), params={"review": True}
            ).status_code
            == 200
        )
        assert client.post("/api/v1/admin/opportunities/sync-sources").status_code == 401
        assert client.post("/api/v1/internal/opportunities/sync").status_code == 404
        if created.status_code == 201:
            _cleanup_source(ops_payload["name"])
    finally:
        _cleanup_user(author_email)
        _cleanup_user(ops_email)


def test_infer_opportunity_type_uses_word_boundaries():
    from app.models.opportunity import OpportunityType
    from app.services.opportunity_relevance import infer_opportunity_type

    def raw(title: str, description: str = "") -> RawOpportunity:
        return RawOpportunity(
            external_id="t",
            title=title,
            organization_name="Example",
            description=description,
            application_url="https://example.com/apply",
        )

    assert infer_opportunity_type(raw("Senior Software Engineer", "Own internal data platforms.")) == OpportunityType.JOB
    assert infer_opportunity_type(raw("Data Engineering Intern")) == OpportunityType.INTERNSHIP
    assert infer_opportunity_type(raw("University Grad – Product Engineer")) == OpportunityType.INTERNSHIP
    assert infer_opportunity_type(raw("ETHGlobal Prague Hackathon")) == OpportunityType.HACKATHON
    assert infer_opportunity_type(raw("Ethereum Ecosystem Grants")) == OpportunityType.GRANT
    assert infer_opportunity_type(raw("Protocol Bug Bounty")) == OpportunityType.BOUNTY
    assert infer_opportunity_type(raw("AI Research Engineer")) == OpportunityType.RESEARCH
    assert infer_opportunity_type(raw("Security Researcher", "We research threats internally.")) == OpportunityType.JOB
