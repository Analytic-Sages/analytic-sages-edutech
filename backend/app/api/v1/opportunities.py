from __future__ import annotations

import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status, Body

from app.api.deps import (
    get_opportunity_digest_service,
    get_opportunity_engagement_service,
    get_opportunity_ingestion_service,
    get_opportunity_review_assist_service,
    get_opportunity_discovery_service,
    get_opportunity_service,
    get_opportunity_telegram_service,
    get_current_user_optional,
    require_opportunity_ops,
    require_public_opportunities_hub,
    require_student,
)
from app.core.config import Settings, get_settings
from app.models.opportunity import (
    BountyCategory,
    EmploymentType,
    ExperienceLevel,
    HackathonEventFormat,
    LocationRegion,
    OpportunityStatus,
    OpportunityType,
    WorkplaceType,
)
from app.models.user import User
from app.schemas.opportunities import (
    AdminTaxonomy,
    OpportunityAdmin,
    OpportunityAdminList,
    OpportunityAdminOverview,
    OpportunityBulkPublishRequest,
    OpportunityBulkPublishResult,
    OpportunityCreate,
    OpportunityDecision,
    OpportunityDiscoverImportRequest,
    OpportunityDiscoverImportResult,
    OpportunityDiscoverRequest,
    OpportunityDiscoverResponse,
    OpportunityFiltersPublic,
    OpportunityListPublic,
    OpportunityPublic,
    OpportunityReviewAssistPublic,
    OpportunityReclassifyResult,
    OpportunitySaveList,
    OpportunitySavePublic,
    OpportunitySourceAdmin,
    OpportunitySourceCreate,
    OpportunitySourceList,
    OpportunitySourceUpdate,
    OpportunitySyncAllResult,
    OpportunitySyncRequest,
    OpportunitySyncRunList,
    OpportunitySyncRunPublic,
    OpportunityUpdate,
    UserCareerInterestsPublic,
    UserCareerInterestsUpdate,
)
from app.services.opportunity_digest import OpportunityDigestService
from app.services.opportunity_discovery import OpportunityDiscoveryService
from app.services.opportunity_ingestion import OpportunityIngestionService
from app.services.opportunity_review_assist import OpportunityReviewAssistService
from app.services.opportunity_saves import OpportunityEngagementService
from app.services.opportunity_telegram import OpportunityTelegramService
from app.services.opportunities import OpportunityService

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities", response_model=OpportunityListPublic)
def list_opportunities(
    _: None = Depends(require_public_opportunities_hub),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    current_user: User | None = Depends(get_current_user_optional),
    q: str | None = Query(default=None, max_length=120),
    opportunity_type: OpportunityType | None = Query(default=None),
    career_path: str | None = Query(default=None, max_length=180),
    skill: str | None = Query(default=None, max_length=120),
    workplace_type: WorkplaceType | None = Query(default=None),
    experience_level: ExperienceLevel | None = Query(default=None),
    employment_type: EmploymentType | None = Query(default=None),
    region: LocationRegion | None = Query(default=None),
    event_format: HackathonEventFormat | None = Query(default=None),
    hackathon_phase: str | None = Query(
        default=None,
        pattern="^(open|upcoming|ongoing|ended|unknown)$",
    ),
    bounty_category: BountyCategory | None = Query(default=None),
    bounty_phase: str | None = Query(
        default=None,
        pattern="^(open|closing_soon|ended|unknown)$",
    ),
    sort: str = Query(
        default="newest",
        pattern="^(newest|deadline|featured|closing_soon|matched|hackathon|bounty)$",
    ),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> OpportunityListPublic:
    return opportunities.list_public(
        q=q,
        opportunity_type=opportunity_type,
        career_path=career_path,
        skill=skill,
        workplace_type=workplace_type,
        experience_level=experience_level,
        employment_type=employment_type,
        region=region,
        event_format=event_format,
        hackathon_phase=hackathon_phase,
        bounty_category=bounty_category,
        bounty_phase=bounty_phase,
        sort=sort,
        limit=limit,
        offset=offset,
        user=current_user,
    )


@router.get("/opportunities/filters", response_model=OpportunityFiltersPublic)
def opportunity_filters(
    _: None = Depends(require_public_opportunities_hub),
    opportunities: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityFiltersPublic:
    return opportunities.list_filters()


@router.get("/opportunities/{slug}", response_model=OpportunityPublic)
def get_opportunity(
    slug: str,
    _: None = Depends(require_public_opportunities_hub),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> OpportunityPublic:
    return opportunities.get_public(slug, user=current_user)


@router.get("/admin/opportunities", response_model=OpportunityAdminList)
def admin_list_opportunities(
    _: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    q: str | None = Query(default=None, max_length=120),
    status_filter: OpportunityStatus | None = Query(default=None, alias="status"),
    review: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> OpportunityAdminList:
    return opportunities.list_admin(
        q=q,
        status_filter=status_filter,
        review_queue=review,
        limit=limit,
        offset=offset,
    )


@router.get("/admin/opportunities/taxonomy", response_model=AdminTaxonomy)
def admin_opportunity_taxonomy(
    _: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
) -> AdminTaxonomy:
    return opportunities.admin_taxonomy()


@router.get("/admin/opportunities/overview", response_model=OpportunityAdminOverview)
def admin_opportunity_overview(
    _: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
) -> OpportunityAdminOverview:
    return ingestion.overview()


@router.post("/admin/opportunities/sync-sources", response_model=OpportunitySyncAllResult)
def admin_sync_opportunity_sources(
    current_user: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
    payload: OpportunitySyncRequest = Body(default_factory=OpportunitySyncRequest),
) -> OpportunitySyncAllResult:
    return ingestion.sync_all_enabled(actor=current_user, source_ids=payload.source_ids)


@router.post("/admin/opportunities/discover", response_model=OpportunityDiscoverResponse)
def admin_discover_opportunities(
    payload: OpportunityDiscoverRequest,
    _: User = Depends(require_opportunity_ops),
    discovery: OpportunityDiscoveryService = Depends(get_opportunity_discovery_service),
) -> OpportunityDiscoverResponse:
    return discovery.discover(types=payload.types, query=payload.query)


@router.post("/admin/opportunities/discover/import", response_model=OpportunityDiscoverImportResult)
def admin_import_discovered_opportunities(
    payload: OpportunityDiscoverImportRequest,
    current_user: User = Depends(require_opportunity_ops),
    discovery: OpportunityDiscoveryService = Depends(get_opportunity_discovery_service),
) -> OpportunityDiscoverImportResult:
    return discovery.import_candidates(payload.candidates, current_user)


@router.post("/admin/opportunities/reclassify-types", response_model=OpportunityReclassifyResult)
def admin_reclassify_opportunity_types(
    _: User = Depends(require_opportunity_ops),
    discovery: OpportunityDiscoveryService = Depends(get_opportunity_discovery_service),
) -> OpportunityReclassifyResult:
    return OpportunityReclassifyResult(updated=discovery.reclassify_drafts())


@router.post("/admin/opportunities/bulk-publish", response_model=OpportunityBulkPublishResult)
def admin_bulk_publish_opportunities(
    payload: OpportunityBulkPublishRequest,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    telegram: OpportunityTelegramService = Depends(get_opportunity_telegram_service),
) -> OpportunityBulkPublishResult:
    result = opportunities.publish_bulk(
        current_user,
        payload.opportunity_ids,
        notes=payload.notes,
        include_high_risk=payload.include_high_risk,
    )
    for opportunity_id in result.published_ids:
        telegram.announce_on_publish(opportunity_id)
    return result


@router.post("/admin/opportunities", response_model=OpportunityAdmin, status_code=status.HTTP_201_CREATED)
def admin_create_opportunity(
    payload: OpportunityCreate,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityAdmin:
    return opportunities.create(payload, current_user)


@router.get("/admin/opportunity-sources", response_model=OpportunitySourceList)
def admin_list_opportunity_sources(
    _: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
) -> OpportunitySourceList:
    return ingestion.list_sources()


@router.post(
    "/admin/opportunity-sources",
    response_model=OpportunitySourceAdmin,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_opportunity_source(
    payload: OpportunitySourceCreate,
    _: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
) -> OpportunitySourceAdmin:
    return ingestion.create_source(payload)


@router.get("/admin/opportunity-sources/{source_id}", response_model=OpportunitySourceAdmin)
def admin_get_opportunity_source(
    source_id: UUID,
    _: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
) -> OpportunitySourceAdmin:
    return ingestion.get_source(source_id)


@router.patch("/admin/opportunity-sources/{source_id}", response_model=OpportunitySourceAdmin)
def admin_update_opportunity_source(
    source_id: UUID,
    payload: OpportunitySourceUpdate,
    _: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
) -> OpportunitySourceAdmin:
    return ingestion.update_source(source_id, payload)


@router.post("/admin/opportunity-sources/{source_id}/sync", response_model=OpportunitySyncRunPublic)
def admin_sync_opportunity_source(
    source_id: UUID,
    current_user: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
) -> OpportunitySyncRunPublic:
    return ingestion.sync_source(source_id, actor=current_user)


@router.get("/admin/opportunity-sources/{source_id}/sync-runs", response_model=OpportunitySyncRunList)
def admin_list_opportunity_sync_runs(
    source_id: UUID,
    _: User = Depends(require_opportunity_ops),
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
    limit: int = Query(default=20, ge=1, le=50),
) -> OpportunitySyncRunList:
    return ingestion.list_sync_runs(source_id, limit=limit)


@router.post("/internal/opportunities/sync")
def internal_sync_opportunities(
    ingestion: OpportunityIngestionService = Depends(get_opportunity_ingestion_service),
    settings: Settings = Depends(get_settings),
    x_opportunity_sync_token: str | None = Header(default=None),
    payload: OpportunitySyncRequest = Body(default_factory=OpportunitySyncRequest),
) -> dict:
    expected = (settings.opportunity_sync_token or "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    provided = (x_opportunity_sync_token or "").strip()
    if len(provided) != len(expected) or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sync token")
    runs = ingestion.sync_enabled_sources(source_ids=payload.source_ids)
    expired = ingestion.expire_past_deadlines()
    return {
        "runs": [run.model_dump(mode="json") for run in runs],
        "expiration": expired,
        "summary": {
            "sources_attempted": len(runs),
            "sources_successful": sum(1 for run in runs if run.status == "completed"),
            "sources_failed": sum(1 for run in runs if run.status == "failed"),
            "found": sum(run.found for run in runs),
            "created": sum(run.created for run in runs),
            "duplicates": sum(run.duplicates for run in runs),
            "rejected": sum(run.rejected for run in runs),
        },
    }


@router.post("/internal/opportunities/digest")
def internal_opportunity_digest(
    digest: OpportunityDigestService = Depends(get_opportunity_digest_service),
    settings: Settings = Depends(get_settings),
    x_opportunity_sync_token: str | None = Header(default=None),
    force: bool = Query(default=False),
) -> dict:
    expected = (settings.opportunity_sync_token or "").strip()
    if not expected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    provided = (x_opportunity_sync_token or "").strip()
    if len(provided) != len(expected) or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sync token")
    return digest.send_weekly(force=force)


@router.get("/me/opportunity-interests", response_model=UserCareerInterestsPublic)
def my_opportunity_interests(
    _: None = Depends(require_public_opportunities_hub),
    current_user: User = Depends(require_student),
    engagement: OpportunityEngagementService = Depends(get_opportunity_engagement_service),
) -> UserCareerInterestsPublic:
    return engagement.get_interests(current_user)


@router.put("/me/opportunity-interests", response_model=UserCareerInterestsPublic)
def update_opportunity_interests(
    payload: UserCareerInterestsUpdate,
    _: None = Depends(require_public_opportunities_hub),
    current_user: User = Depends(require_student),
    engagement: OpportunityEngagementService = Depends(get_opportunity_engagement_service),
) -> UserCareerInterestsPublic:
    return engagement.set_interests(current_user, payload.career_path_ids)


@router.get("/me/opportunities", response_model=OpportunitySaveList)
def my_saved_opportunities(
    _: None = Depends(require_public_opportunities_hub),
    current_user: User = Depends(require_student),
    engagement: OpportunityEngagementService = Depends(get_opportunity_engagement_service),
    bucket: str = Query(default="saved", pattern="^(saved|applied|closed)$"),
) -> OpportunitySaveList:
    return engagement.list_saved(current_user, bucket=bucket)


@router.post("/me/opportunities/{opportunity_id}/save", response_model=OpportunitySavePublic)
def save_opportunity(
    opportunity_id: UUID,
    _: None = Depends(require_public_opportunities_hub),
    current_user: User = Depends(require_student),
    engagement: OpportunityEngagementService = Depends(get_opportunity_engagement_service),
) -> OpportunitySavePublic:
    return engagement.save(current_user, opportunity_id)


@router.post("/me/opportunities/{opportunity_id}/applied", response_model=OpportunitySavePublic)
def mark_opportunity_applied(
    opportunity_id: UUID,
    _: None = Depends(require_public_opportunities_hub),
    current_user: User = Depends(require_student),
    engagement: OpportunityEngagementService = Depends(get_opportunity_engagement_service),
) -> OpportunitySavePublic:
    return engagement.mark_applied(current_user, opportunity_id)


@router.delete(
    "/me/opportunities/{opportunity_id}/save",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def unsave_opportunity(
    opportunity_id: UUID,
    _: None = Depends(require_public_opportunities_hub),
    current_user: User = Depends(require_student),
    engagement: OpportunityEngagementService = Depends(get_opportunity_engagement_service),
) -> None:
    engagement.unsave(current_user, opportunity_id)


@router.get("/admin/opportunities/{opportunity_id}", response_model=OpportunityAdmin)
def admin_get_opportunity(
    opportunity_id: UUID,
    _: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityAdmin:
    return opportunities.get_admin(opportunity_id)


@router.patch("/admin/opportunities/{opportunity_id}", response_model=OpportunityAdmin)
def admin_update_opportunity(
    opportunity_id: UUID,
    payload: OpportunityUpdate,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
) -> OpportunityAdmin:
    return opportunities.update(opportunity_id, payload, current_user)


@router.post("/admin/opportunities/{opportunity_id}/publish", response_model=OpportunityAdmin)
def admin_publish_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    telegram: OpportunityTelegramService = Depends(get_opportunity_telegram_service),
    payload: OpportunityDecision = OpportunityDecision(),
) -> OpportunityAdmin:
    result = opportunities.publish(opportunity_id, current_user, notes=payload.notes)
    telegram.announce_on_publish(opportunity_id)
    return result


@router.post("/admin/opportunities/{opportunity_id}/announce")
def admin_announce_opportunity(
    opportunity_id: UUID,
    _: User = Depends(require_opportunity_ops),
    telegram: OpportunityTelegramService = Depends(get_opportunity_telegram_service),
    force: bool = Query(default=False),
) -> dict:
    return telegram.announce(opportunity_id, force=force)


@router.post("/admin/opportunities/{opportunity_id}/review-assist", response_model=OpportunityReviewAssistPublic)
def admin_review_assist(
    opportunity_id: UUID,
    _: User = Depends(require_opportunity_ops),
    assist: OpportunityReviewAssistService = Depends(get_opportunity_review_assist_service),
) -> OpportunityReviewAssistPublic:
    return assist.review(opportunity_id)


@router.post("/admin/opportunities/digest")
def admin_send_opportunity_digest(
    current_user: User = Depends(require_opportunity_ops),
    digest: OpportunityDigestService = Depends(get_opportunity_digest_service),
    force: bool = Query(default=False),
) -> dict:
    return digest.send_weekly(actor=current_user, force=force)


@router.post("/admin/opportunities/{opportunity_id}/unpublish", response_model=OpportunityAdmin)
def admin_unpublish_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    payload: OpportunityDecision = OpportunityDecision(),
) -> OpportunityAdmin:
    return opportunities.unpublish(opportunity_id, current_user, notes=payload.notes)


@router.post("/admin/opportunities/{opportunity_id}/reject", response_model=OpportunityAdmin)
def admin_reject_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    payload: OpportunityDecision = OpportunityDecision(),
) -> OpportunityAdmin:
    return opportunities.reject(opportunity_id, current_user, notes=payload.notes)


@router.post("/admin/opportunities/{opportunity_id}/archive", response_model=OpportunityAdmin)
def admin_archive_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(require_opportunity_ops),
    opportunities: OpportunityService = Depends(get_opportunity_service),
    payload: OpportunityDecision = OpportunityDecision(),
) -> OpportunityAdmin:
    return opportunities.archive(opportunity_id, current_user, notes=payload.notes)
