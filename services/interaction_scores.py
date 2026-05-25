from fastapi import HTTPException
from db import supabase


def get_by_interaction(interaction_id: str):
    """Scores de una interacción con su detalle anidado (FK: interaction_scores.interaction_id)."""
    return (
        supabase.table("interaction_scores")
        .select("*, interactions(*, campaigns(*))")
        .eq("interaction_id", interaction_id)
        .execute()
        .data
    )


def get_by_id(score_id: str):
    response = (
        supabase.table("interaction_scores")
        .select("*, interactions(*)")
        .eq("id", score_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction score not found")
    return response.data[0]


def create(data: dict):
    return supabase.table("interaction_scores").insert(data).execute().data[0]


def update(score_id: str, data: dict):
    response = (
        supabase.table("interaction_scores").update(data).eq("id", score_id).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction score not found")
    return response.data[0]


def delete(score_id: str):
    response = (
        supabase.table("interaction_scores").delete().eq("id", score_id).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction score not found")
