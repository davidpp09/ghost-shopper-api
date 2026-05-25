from fastapi import APIRouter
from models.schemas import BotCallRequest, SuccessResponse
from utils import success_response, ERROR_RESPONSES
import services.bot as bot_service

router = APIRouter(prefix="/bot", tags=["Bot"])


@router.post("/call", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def bot_call(body: BotCallRequest):
    """
    Endpoint todo-en-uno para el webscraper.
    Recibe phone + context (texto libre con datos de la empresa).
    Con IA extrae los datos, crea empresa + campaña + interacción y dispara la llamada.
    """
    data = bot_service.launch_bot_call(body.phone, body.context or "")
    return success_response(data, status_code=201)
