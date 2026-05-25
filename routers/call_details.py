from fastapi import APIRouter
from models.schemas import CallDetailCreate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.call_details as call_detail_service

router = APIRouter(prefix="/call-details", tags=["Call Details"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_call_detail(call_detail: CallDetailCreate):
    data = call_detail_service.create(call_detail.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/interaction/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_call_details_by_interaction(interaction_id: UUID):
    data = call_detail_service.get_by_interaction(str(interaction_id))
    return success_response(data)
