from fastapi import APIRouter
from models.schemas import MessageCreate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.messages as message_service

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_message(message: MessageCreate):
    data = message_service.create(message.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/interaction/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_messages_by_interaction(interaction_id: UUID):
    data = message_service.get_by_interaction(str(interaction_id))
    return success_response(data)
