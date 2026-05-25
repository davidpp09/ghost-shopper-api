from fastapi import APIRouter, Query
from uuid import UUID
from models.schemas import CompanyCreate, CompanyUpdate, SuccessResponse
from utils import success_response, ERROR_RESPONSES
import services.companies as company_service

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.post("/", response_model=SuccessResponse, responses=ERROR_RESPONSES, status_code=201)
def create_company(company: CompanyCreate):
    data = company_service.create(company.model_dump(mode="json", exclude_unset=True))
    return success_response(data, status_code=201)

@router.get("/", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_companies(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    items = company_service.get_all(limit, offset)
    return success_response({"items": items, "limit": limit, "offset": offset})

@router.get("/{company_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def get_company(company_id: UUID):
    data = company_service.get_by_id(str(company_id))
    return success_response(data)

@router.patch("/{company_id}", response_model=SuccessResponse, responses=ERROR_RESPONSES)
def update_company(company_id: UUID, body: CompanyUpdate):
    changes = body.model_dump(mode="json", exclude_unset=True)
    data = company_service.update(str(company_id), changes)
    return success_response(data)
