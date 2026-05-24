import os
import json
from datetime import date
from fastapi import HTTPException
from groq import Groq
from db import supabase

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = """Eres un consultor experto en mystery shopping para inmobiliarias.
Se te darán métricas de una campaña de evaluación de atención al cliente.
Genera un análisis profesional en español.

Devuelve ÚNICAMENTE este JSON:
{
  "findings": {
    "resumen": string,
    "fortalezas": [string],
    "debilidades": [string]
  },
  "recommendations": {
    "prioritarias": [string],
    "secundarias": [string]
  }
}"""


def _calculate_metrics(scores: list) -> dict:
    """Calcula todas las métricas en código puro — sin IA."""
    total = len(scores)
    if total == 0:
        return {}

    responded       = sum(1 for s in scores if s.get("responded"))
    gave_price      = sum(1 for s in scores if s.get("gave_price"))
    did_followup    = sum(1 for s in scores if s.get("did_followup"))
    used_name       = sum(1 for s in scores if s.get("used_name"))
    attempted_close = sum(1 for s in scores if s.get("attempted_close"))

    quality_scores = [s["quality_score"] for s in scores if s.get("quality_score") is not None]
    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None

    return {
        "total_interactions": total,
        "response_rate_pct":       round(responded       / total * 100, 1),
        "gave_price_pct":          round(gave_price       / total * 100, 1),
        "followup_rate_pct":       round(did_followup     / total * 100, 1),
        "used_name_pct":           round(used_name        / total * 100, 1),
        "attempted_close_pct":     round(attempted_close  / total * 100, 1),
        "avg_quality_score":       avg_quality,
    }


def _build_summary_text(metrics: dict, campaign: dict) -> str:
    """Construye el texto de resumen para el prompt — corto y directo."""
    company_name = (campaign.get("companies") or {}).get("name", "la empresa")
    lines = [
        f"Empresa evaluada: {company_name}",
        f"Total de interacciones analizadas: {metrics['total_interactions']}",
        f"Tasa de respuesta: {metrics['response_rate_pct']}%",
        f"Dio precio proactivamente: {metrics['gave_price_pct']}%",
        f"Realizó seguimiento: {metrics['followup_rate_pct']}%",
        f"Usó el nombre del cliente: {metrics['used_name_pct']}%",
        f"Intentó cerrar la venta: {metrics['attempted_close_pct']}%",
        f"Score promedio de calidad: {metrics['avg_quality_score']}/100",
    ]
    return "\n".join(lines)


def generate_report(campaign_id: str) -> dict:
    """
    Calcula métricas con código puro y usa Groq solo para redactar
    findings y recommendations. Guarda el reporte en la tabla reports.
    """
    campaign_resp = (
        supabase.table("campaigns")
        .select("*, companies(*)")
        .eq("id", campaign_id)
        .execute()
    )
    if not campaign_resp.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = campaign_resp.data[0]

    interactions_resp = (
        supabase.table("interactions")
        .select("id")
        .eq("campaign_id", campaign_id)
        .execute()
    )
    interaction_ids = [i["id"] for i in (interactions_resp.data or [])]

    if not interaction_ids:
        raise HTTPException(
            status_code=422,
            detail="La campaña no tiene interacciones para generar un reporte",
        )

    scores_resp = (
        supabase.table("interaction_scores")
        .select("*")
        .in_("interaction_id", interaction_ids)
        .execute()
    )
    scores = scores_resp.data or []

    if not scores:
        raise HTTPException(
            status_code=422,
            detail="Las interacciones no tienen scores aún — ejecuta el análisis primero",
        )

    metrics = _calculate_metrics(scores)
    summary_text = _build_summary_text(metrics, campaign)

    chat_response = _client.chat.completions.create(
        model=_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": summary_text},
        ],
        temperature=0.3,
    )

    raw = chat_response.choices[0].message.content
    try:
        ai_result = json.loads(raw)
        if not isinstance(ai_result, dict):
            raise ValueError(f"Tipo inesperado: {type(ai_result).__name__}")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=502, detail=f"Groq devolvió respuesta inválida: {e}")

    report_data = {
        "campaign_id": campaign_id,
        "period_start": campaign.get("start_date"),
        "period_end": str(date.today()),
        "metrics": metrics,
        "findings": ai_result.get("findings", {}),
        "recommendations": ai_result.get("recommendations", {}),
        "status": "draft",
    }

    saved = supabase.table("reports").insert(report_data).execute()
    if not saved.data:
        raise HTTPException(status_code=500, detail="No se pudo guardar el reporte")

    return saved.data[0]
