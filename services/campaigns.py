from fastapi import HTTPException
from db import supabase


def get_all(limit: int, offset: int):
    """Lista de campañas con su empresa incluida (FK: campaigns.company_id)."""
    return (
        supabase.table("campaigns")
        .select("*, companies(*)")
        .range(offset, offset + limit - 1)
        .execute()
        .data
    )


def get_by_id(campaign_id: str):
    """Campaña con su empresa e interacciones anidadas.

    Relaciones usadas:
      - campaigns.company_id → companies.id
      - interactions.campaign_id → campaigns.id
    """
    response = (
        supabase.table("campaigns")
        .select("*, companies(*), interactions(*)")
        .eq("id", campaign_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return response.data[0]


def create(data: dict):
    return supabase.table("campaigns").insert(data).execute().data[0]


def update(campaign_id: str, data: dict):
    response = supabase.table("campaigns").update(data).eq("id", campaign_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return response.data[0]


def delete(campaign_id: str):
    response = supabase.table("campaigns").delete().eq("id", campaign_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
