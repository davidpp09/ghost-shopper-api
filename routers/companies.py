from fastapi import APIRouter, HTTPException, Query
from models.schemas import CompanyCreate, CompanyUpdate, SuccessResponse
from uuid import UUID
from utils import success_response, ERROR_RESPONSES
import services.companies as company_service

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_company(company: CompanyCreate):
    data = company_service.create(company.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_companies(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    items = company_service.get_all(limit, offset)
    return success_response({"items": items, "limit": limit, "offset": offset})

@router.get("/{company_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_company(company_id: UUID):
    data = company_service.get_by_id(str(company_id))
    return success_response(data)

@router.patch("/{company_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def update_company(company_id: UUID, company: CompanyUpdate):
    data = company.model_dump(mode="json", exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    result = company_service.update(str(company_id), data)
    return success_response(result)

@router.delete("/{company_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def delete_company(company_id: UUID):
    company_service.delete(str(company_id))
    return success_response({"message": "Company deleted"})
