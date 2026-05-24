from fastapi import HTTPException
from db import supabase


def get_by_campaign(campaign_id: str):
    return (
        supabase.table("reports")
        .select("*")
        .eq("campaign_id", campaign_id)
        .execute()
        .data
    )


def get_by_id(report_id: str):
    response = supabase.table("reports").select("*").eq("id", report_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Report not found")
    return response.data[0]


def create(data: dict):
    return supabase.table("reports").insert(data).execute().data[0]
