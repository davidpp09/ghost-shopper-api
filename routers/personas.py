from fastapi import APIRouter, HTTPException, Query
from models.schemas import PersonaCreate, PersonaUpdate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.personas as persona_service

router = APIRouter(prefix="/personas", tags=["Personas"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_persona(persona: PersonaCreate):
    data = persona_service.create(persona.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_personas(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    items = persona_service.get_all(limit, offset)
    return success_response({"items": items, "limit": limit, "offset": offset})

@router.get("/{persona_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_persona(persona_id: UUID):
    data = persona_service.get_by_id(str(persona_id))
    return success_response(data)

@router.patch("/{persona_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def update_persona(persona_id: UUID, persona: PersonaUpdate):
    data = persona.model_dump(mode="json", exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    result = persona_service.update(str(persona_id), data)
    return success_response(result)

@router.delete("/{persona_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def delete_persona(persona_id: UUID):
    persona_service.delete(str(persona_id))
    return success_response({"message": "Persona deleted"})
