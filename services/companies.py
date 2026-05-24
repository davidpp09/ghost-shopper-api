from fastapi import HTTPException
from db import supabase


def get_all(limit: int, offset: int):
    return (
        supabase.table("companies")
        .select("*")
        .range(offset, offset + limit - 1)
        .execute()
        .data
    )


def get_by_id(company_id: str):
    """Trae la empresa con todas sus campañas anidadas (FK: campaigns.company_id)."""
    response = (
        supabase.table("companies")
        .select("*, campaigns(*)")
        .eq("id", company_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Company not found")
    return response.data[0]


def create(data: dict):
    return supabase.table("companies").insert(data).execute().data[0]


def update(company_id: str, data: dict):
    response = supabase.table("companies").update(data).eq("id", company_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Company not found")
    return response.data[0]


def delete(company_id: str):
    response = supabase.table("companies").delete().eq("id", company_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Company not found")
