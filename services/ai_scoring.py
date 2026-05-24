import os
import json
import traceback
from datetime import datetime, timezone
from fastapi import HTTPException
from groq import Groq
from db import supabase
from parsers.transcript import parse_transcript

_SLOW_RESPONSE_THRESHOLD_SEC = 4 * 60 * 60  # 4 horas

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = """Eres un evaluador de mystery shopping (cliente incógnito).
Analiza la conversación y evalúa qué tan bien atendió la empresa al cliente potencial.
El quality_score ya tiene penalizaciones por tiempo de respuesta aplicadas — no las recalcules.

Devuelve ÚNICAMENTE este JSON:
{
  "responded": bool,
  "gave_price": bool,
  "did_followup": bool,
  "used_name": bool,
  "attempted_close": bool,
  "quality_score": int,
  "reasoning": string
}"""


def _build_transcript_text(interaction: dict) -> str:
    """Construye el texto del transcript a partir de call_details o messages."""
    lines = []

    call_details = interaction.get("call_details") or []
    for cd in call_details:
        transcript = parse_transcript(cd.get("transcript"))
        for turn in transcript:
                role = turn.get("role", "unknown").upper()
                msg = turn.get("message", "").strip()
                if msg:
                    lines.append(f"[{role}]: {msg}")
        duration = cd.get("duration_sec")
        outcome = cd.get("outcome")
        if outcome:
            lines.append(f"\n[RESULTADO DE LLAMADA: {outcome}, duración: {duration}s]")

    messages = interaction.get("messages") or []
    for msg in sorted(messages, key=lambda m: m.get("sent_at", "")):
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"[{role}]: {content}")

    return "\n".join(lines) if lines else ""


def _build_context_text(interaction: dict) -> str:
    """Construye contexto de campaña y persona para el prompt."""
    parts = []

    persona = interaction.get("personas") or {}
    if persona:
        parts.append(
            f"Persona usada: {persona.get('name')} "
            f"(empresa ficticia: {persona.get('fake_company')}, "
            f"rol: {persona.get('role')})"
        )

    campaign = interaction.get("campaigns") or {}
    if campaign:
        company = campaign.get("companies") or {}
        parts.append(f"Empresa evaluada: {company.get('name', 'desconocida')}")
        parts.append(f"Canal: {interaction.get('channel', 'desconocido')}")

    return "\n".join(parts)


def _parse_ts(ts_str: str) -> datetime | None:
    """Parsea un timestamp ISO de Supabase a datetime con timezone."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _classify_response_time(sec: float) -> tuple[str, int]:
    """Clasifica un tiempo de respuesta y devuelve (etiqueta, penalización)."""
    if sec < 1800:       # < 30 min
        return "Excelente", 0
    if sec < 3600:       # 30 min – 1 hora
        return "Aceptable", -5
    if sec < 14400:      # 1 – 4 horas
        return "Lento", -15
    return "Crítico", -30


def _build_timing_context(messages: list) -> tuple[str, int]:
    """
    Calcula tiempos de respuesta en código puro y devuelve (texto_para_prompt, penalización_total).
    La penalización se aplica al quality_score antes de llamar a la IA,
    así el modelo no necesita hacer matemáticas — solo leer el transcript.
    """
    if not messages:
        return "", 0

    sorted_msgs = sorted(messages, key=lambda m: m.get("sent_at", ""))

    gaps = []
    for i, msg in enumerate(sorted_msgs):
        if msg.get("role") != "agent":
            continue
        ts_sent = _parse_ts(msg.get("sent_at", ""))
        if not ts_sent:
            continue
        for next_msg in sorted_msgs[i + 1:]:
            if next_msg.get("role") == "user":
                ts_reply = _parse_ts(next_msg.get("sent_at", ""))
                if ts_reply:
                    gaps.append((ts_reply - ts_sent).total_seconds())
                break

    if not gaps:
        return "", 0

    def fmt(sec: float) -> str:
        if sec < 60:
            return f"{int(sec)}s"
        if sec < 3600:
            return f"{int(sec // 60)}min"
        return f"{sec / 3600:.1f}h"

    avg_sec = sum(gaps) / len(gaps)
    max_sec = max(gaps)
    label, penalty = _classify_response_time(max_sec)
    total_penalty = sum(_classify_response_time(g)[1] for g in gaps)

    text = (
        f"Tiempo de respuesta — {label} "
        f"(promedio: {fmt(avg_sec)}, máximo: {fmt(max_sec)}, "
        f"penalización ya aplicada al score: {total_penalty} pts)"
    )
    return text, total_penalty


def analyze_interaction(interaction_id: str) -> dict:
    """
    Obtiene la interacción completa, la analiza con Groq y guarda el score.
    Devuelve el registro creado en interaction_scores.
    """
    try:
        response = (
            supabase.table("interactions")
            .select("*, campaigns(*, companies(*)), personas(*)")
            .eq("id", interaction_id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar Supabase: {traceback.format_exc()}")

    if not response.data:
        raise HTTPException(status_code=404, detail="Interaction not found")

    interaction = response.data[0]

    existing = (
        supabase.table("interaction_scores")
        .select("id")
        .eq("interaction_id", interaction_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="Esta interacción ya tiene un score. Consulta GET /interaction-scores/interaction/{id}",
        )

    interaction["call_details"] = (
        supabase.table("call_details").select("*").eq("interaction_id", interaction_id).execute().data or []
    )
    interaction["messages"] = (
        supabase.table("messages").select("*").eq("interaction_id", interaction_id).execute().data or []
    )

    try:
        transcript_text = _build_transcript_text(interaction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en _build_transcript_text: {traceback.format_exc()}")
    if not transcript_text:
        raise HTTPException(
            status_code=422,
            detail="La interacción no tiene transcript ni mensajes para analizar",
        )

    context_text = _build_context_text(interaction)
    timing_text, timing_penalty = _build_timing_context(interaction.get("messages") or [])

    user_message = f"{context_text}\n\nTRANSCRIPCIÓN:\n{transcript_text}"
    if timing_text:
        user_message += f"\n\n{timing_text}"

    chat_response = _client.chat.completions.create(
        model=_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
    )

    raw = chat_response.choices[0].message.content
    try:
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError(f"Se esperaba dict, llegó {type(result).__name__}: {raw}")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=502, detail=f"Groq devolvió respuesta inválida: {e} | raw: {raw}")

    base_score = result.get("quality_score") or 0
    final_score = max(0, min(100, base_score + timing_penalty))

    score_data = {
        "interaction_id": interaction_id,
        "responded": result.get("responded", False),
        "gave_price": result.get("gave_price", False),
        "did_followup": result.get("did_followup", False),
        "used_name": result.get("used_name", False),
        "attempted_close": result.get("attempted_close", False),
        "quality_score": final_score,
        "scored_by": "ai",
    }

    saved = supabase.table("interaction_scores").insert(score_data).execute()
    if not saved.data:
        raise HTTPException(status_code=500, detail="No se pudo guardar el score")

    return {**saved.data[0], "reasoning": result.get("reasoning", "")}
