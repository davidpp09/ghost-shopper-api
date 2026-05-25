from fastapi import HTTPException
from db import supabase


def get_all(limit: int, offset: int):
    """Lista de interacciones con su campaña incluida."""
    return (
        supabase.table("interactions")
        .select("*, campaigns(*)")
        .range(offset, offset + limit - 1)
        .execute()
        .data
    )


def get_by_id(interaction_id: str):
    """Interacción completa con campaña y todos sus mensajes.

    Relaciones usadas:
      - interactions.campaign_id → campaigns.id
      - messages.interaction_id → interactions.id
    """
    response = (
        supabase.table("interactions")
        .select("*, campaigns(*), messages(*)")
        .eq("id", interaction_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return response.data[0]


def get_by_campaign(campaign_id: str):
    """Interacciones de una campaña con su score anidado (para la tabla del dashboard)."""
    return (
        supabase.table("interactions")
        .select("*, interaction_scores(*)")
        .eq("campaign_id", campaign_id)
        .order("initiated_at", desc=True)
        .execute()
        .data
    )


def create(data: dict):
    # El router usa exclude_unset, así que el default "sent" de Pydantic se pierde.
    # Lo forzamos aquí para que la columna nunca quede en NULL.
    data.setdefault("status", "sent")
    return supabase.table("interactions").insert(data).execute().data[0]


def update(interaction_id: str, data: dict):
    response = (
        supabase.table("interactions").update(data).eq("id", interaction_id).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return response.data[0]


def delete(interaction_id: str):
    response = supabase.table("interactions").delete().eq("id", interaction_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction not found")
