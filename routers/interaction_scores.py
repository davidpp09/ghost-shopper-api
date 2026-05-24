from fastapi import APIRouter, HTTPException
from models.schemas import InteractionScoreCreate, InteractionScoreUpdate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.interaction_scores as score_service

router = APIRouter(prefix="/interaction-scores", tags=["Interaction Scores"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_score(score: InteractionScoreCreate):
    data = score_service.create(score.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/interaction/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_scores_by_interaction(interaction_id: UUID):
    data = score_service.get_by_interaction(str(interaction_id))
    return success_response(data)

@router.get("/{score_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_score(score_id: UUID):
    data = score_service.get_by_id(str(score_id))
    return success_response(data)

@router.patch("/{score_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def update_score(score_id: UUID, score: InteractionScoreUpdate):
    data = score.model_dump(mode="json", exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    result = score_service.update(str(score_id), data)
    return success_response(result)

@router.delete("/{score_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def delete_score(score_id: UUID):
    score_service.delete(str(score_id))
    return success_response({"message": "Interaction score deleted"})
