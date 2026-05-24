from fastapi import HTTPException
from db import supabase


def get_all(limit: int, offset: int):
    """Lista de interacciones con su campaña y persona incluidas."""
    return (
        supabase.table("interactions")
        .select("*, campaigns(*), personas(*)")
        .range(offset, offset + limit - 1)
        .execute()
        .data
    )


def get_by_id(interaction_id: str):
    """Interacción completa con campaña, persona y todos sus mensajes.

    Relaciones usadas:
      - interactions.campaign_id → campaigns.id
      - interactions.persona_id → personas.id
      - messages.interaction_id → interactions.id
    """
    response = (
        supabase.table("interactions")
        .select("*, campaigns(*), personas(*), messages(*)")
        .eq("id", interaction_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return response.data[0]


def create(data: dict):
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
