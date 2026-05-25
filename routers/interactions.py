from fastapi import APIRouter
from models.schemas import InteractionCreate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.interactions as interaction_service
import services.ai_scoring as ai_scoring_service
import services.calls as calls_service

router = APIRouter(prefix="/interactions", tags=["Interactions"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_interaction(interaction: InteractionCreate):
    data = interaction_service.create(interaction.model_dump(mode="json", exclude_unset=True))

    # Si el canal es llamada, disparar la llamada automáticamente
    if interaction.channel == "call":
        call_data = calls_service.initiate_call(data["id"])
        data["call"] = call_data

    return success_response(data, status_code=201)


@router.get("/campaign/{campaign_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_interactions_by_campaign(campaign_id: UUID):
    data = interaction_service.get_by_campaign(str(campaign_id))
    return success_response(data)


@router.get("/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_interaction(interaction_id: UUID):
    data = interaction_service.get_by_id(str(interaction_id))
    return success_response(data)


@router.post("/{interaction_id}/close", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def close_interaction(interaction_id: UUID):
    interaction_service.update(str(interaction_id), {"status": "answered"})
    score = ai_scoring_service.analyze_interaction(str(interaction_id))
    return success_response({"message": "Sesión cerrada y analizada", "score": score})
