from fastapi import HTTPException
from db import supabase


def get_by_interaction(interaction_id: str):
    return (
        supabase.table("messages")
        .select("*")
        .eq("interaction_id", interaction_id)
        .execute()
        .data
    )


def get_by_id(message_id: str):
    response = supabase.table("messages").select("*").eq("id", message_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Message not found")
    return response.data[0]


def create(data: dict):
    return supabase.table("messages").insert(data).execute().data[0]
