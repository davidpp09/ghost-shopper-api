from fastapi import APIRouter
from models.schemas import SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.interaction_scores as score_service
import services.ai_scoring as ai_scoring_service

router = APIRouter(prefix="/interaction-scores", tags=["Interaction Scores"])

@router.post("/analyze/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def analyze_interaction(interaction_id: UUID):
    data = ai_scoring_service.analyze_interaction(str(interaction_id))
    return success_response(data, status_code=201)

@router.post("/run-pending", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def run_pending():
    """Evalúa todas las interacciones pendientes que ya estén listas (lo mismo que corre el scheduler)."""
    data = ai_scoring_service.score_pending()
    return success_response(data)

@router.get("/interaction/{interaction_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_scores_by_interaction(interaction_id: UUID):
    data = score_service.get_by_interaction(str(interaction_id))
    return success_response(data)
