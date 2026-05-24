from fastapi import APIRouter
from models.schemas import ReportCreate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.reports as report_service

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_report(report: ReportCreate):
    data = report_service.create(report.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/campaign/{campaign_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_reports_by_campaign(campaign_id: UUID):
    data = report_service.get_by_campaign(str(campaign_id))
    return success_response(data)

@router.get("/{report_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_report(report_id: UUID):
    data = report_service.get_by_id(str(report_id))
    return success_response(data)
