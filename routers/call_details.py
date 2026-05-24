from fastapi import APIRouter, HTTPException
from models.schemas import CallDetailCreate, CallDetailUpdate, SuccessResponse
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

@router.get("/{call_detail_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_call_detail(call_detail_id: UUID):
    data = call_detail_service.get_by_id(str(call_detail_id))
    return success_response(data)

@router.patch("/{call_detail_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def update_call_detail(call_detail_id: UUID, call_detail: CallDetailUpdate):
    data = call_detail.model_dump(mode="json", exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    result = call_detail_service.update(str(call_detail_id), data)
    return success_response(result)

@router.delete("/{call_detail_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def delete_call_detail(call_detail_id: UUID):
    call_detail_service.delete(str(call_detail_id))
    return success_response({"message": "Call detail deleted"})
