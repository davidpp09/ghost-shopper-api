from fastapi import APIRouter, HTTPException, Query
from models.schemas import InteractionCreate, InteractionUpdate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.interactions as interaction_service
import services.ai_scoring as ai_scoring_service

router = APIRouter(prefix="/interactions", tags=["Interactions"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_interaction(interaction: InteractionCreate):
    data = interaction_service.create(interaction.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_interactions(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    items = interaction_service.get_all(limit, offset)
    return success_response({"items": items, "limit": limit, "offset": offset})

@router.get("/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_interaction(interaction_id: UUID):
    data = interaction_service.get_by_id(str(interaction_id))
    return success_response(data)

@router.patch("/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def update_interaction(interaction_id: UUID, interaction: InteractionUpdate):
    data = interaction.model_dump(mode="json", exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    result = interaction_service.update(str(interaction_id), data)
    return success_response(result)

@router.delete("/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def delete_interaction(interaction_id: UUID):
    interaction_service.delete(str(interaction_id))
    return success_response({"message": "Interaction deleted"})


@router.post("/{interaction_id}/close", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def close_interaction(interaction_id: UUID):
    interaction_service.update(str(interaction_id), {"status": "answered"})
    score = ai_scoring_service.analyze_interaction(str(interaction_id))
    return success_response({"message": "Sesión cerrada y analizada", "score": score})
