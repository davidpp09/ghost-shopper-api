from fastapi import HTTPException
from db import supabase


def get_all(limit: int, offset: int):
    return (
        supabase.table("personas")
        .select("*")
        .range(offset, offset + limit - 1)
        .execute()
        .data
    )


def get_by_id(persona_id: str):
    response = supabase.table("personas").select("*").eq("id", persona_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Persona not found")
    return response.data[0]


def create(data: dict):
    return supabase.table("personas").insert(data).execute().data[0]


def update(persona_id: str, data: dict):
    response = supabase.table("personas").update(data).eq("id", persona_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Persona not found")
    return response.data[0]


def delete(persona_id: str):
    response = supabase.table("personas").delete().eq("id", persona_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Persona not found")
