from fastapi import APIRouter, Query
from uuid import UUID
from models.schemas import CampaignCreate, SuccessResponse
from utils import success_response, ERROR_RESPONSES
import services.campaigns as campaign_service

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_campaign(campaign: CampaignCreate):
    data = campaign_service.create(campaign.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_campaigns(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    items = campaign_service.get_all(limit, offset)
    return success_response({"items": items, "limit": limit, "offset": offset})

@router.get("/{campaign_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_campaign(campaign_id: UUID):
    data = campaign_service.get_by_id(str(campaign_id))
    return success_response(data)
