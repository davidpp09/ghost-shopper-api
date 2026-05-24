from fastapi import HTTPException
from db import supabase
from parsers.transcript import parse_transcript


def _clean(record: dict) -> dict:
    """Aplica el parser de transcript a un registro antes de devolverlo."""
    if record and "transcript" in record:
        record["transcript"] = parse_transcript(record["transcript"])
    return record


def get_by_interaction(interaction_id: str):
    """Todos los call details de una interacción con transcript limpio."""
    data = (
        supabase.table("call_details")
        .select("*")
        .eq("interaction_id", interaction_id)
        .execute()
        .data
    )
    return [_clean(record) for record in data]


def get_by_id(call_detail_id: str):
    """Call detail con transcript limpio."""
    response = (
        supabase.table("call_details")
        .select("*")
        .eq("id", call_detail_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Call detail not found")
    return _clean(response.data[0])


def create(data: dict):
    """Limpia el transcript antes de guardar para que siempre quede en formato estándar."""
    if "transcript" in data:
        data["transcript"] = parse_transcript(data["transcript"])
    return supabase.table("call_details").insert(data).execute().data[0]


def update(call_detail_id: str, data: dict):
    response = (
        supabase.table("call_details").update(data).eq("id", call_detail_id).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Call detail not found")
    return _clean(response.data[0])


def delete(call_detail_id: str):
    response = (
        supabase.table("call_details").delete().eq("id", call_detail_id).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Call detail not found")
