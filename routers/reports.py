from fastapi import APIRouter
from models.schemas import SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.reports as report_service
import services.ai_reports as ai_reports_service

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate/{campaign_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def generate_report(campaign_id: UUID):
    data = ai_reports_service.generate_report(str(campaign_id))
    return success_response(data, status_code=201)

@router.get("/campaign/{campaign_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_reports_by_campaign(campaign_id: UUID):
    data = report_service.get_by_campaign(str(campaign_id))
    return success_response(data)
