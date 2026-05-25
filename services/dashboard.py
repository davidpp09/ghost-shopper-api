from db import supabase


def get_summary() -> dict:
    """KPIs globales para el home del dashboard. Todo calculado en código, sin IA."""
    companies    = supabase.table("companies").select("id").execute().data or []
    campaigns    = supabase.table("campaigns").select("id, status").execute().data or []
    interactions = supabase.table("interactions").select("id, channel, status").execute().data or []
    scores       = supabase.table("interaction_scores").select("quality_score, responded").execute().data or []
    reports      = supabase.table("reports").select("id").execute().data or []

    quality = [s["quality_score"] for s in scores if s.get("quality_score") is not None]
    avg_quality = round(sum(quality) / len(quality), 1) if quality else None

    responded = sum(1 for s in scores if s.get("responded"))
    response_rate = round(responded / len(scores) * 100, 1) if scores else None

    by_channel = {}
    for i in interactions:
        ch = i.get("channel") or "desconocido"
        by_channel[ch] = by_channel.get(ch, 0) + 1

    active_campaigns = sum(1 for c in campaigns if c.get("status") == "active")

    return {
        "total_companies": len(companies),
        "total_campaigns": len(campaigns),
        "active_campaigns": active_campaigns,
        "total_interactions": len(interactions),
        "scored_interactions": len(scores),
        "pending_scoring": len(interactions) - len(scores),
        "avg_quality_score": avg_quality,
        "response_rate_pct": response_rate,
        "total_reports": len(reports),
        "interactions_by_channel": by_channel,
    }
