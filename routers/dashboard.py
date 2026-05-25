from fastapi import APIRouter
from models.schemas import SuccessResponse
from utils import success_response, ERROR_RESPONSES
import services.dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_summary():
    data = dashboard_service.get_summary()
    return success_response(data)
