import os
import json
import traceback
from datetime import datetime, timezone
from fastapi import HTTPException
from groq import Groq
from db import supabase
from parsers.transcript import parse_transcript

_WHATSAPP_TIMEOUT_SEC = 4 * 60 * 60  # 4 horas sin respuesta = sesión finalizada

# Los datos llegan con roles distintos según el canal:
#   - llamadas (ElevenLabs): "agent" / "user"
#   - whatsapp (Make):       "bot"   / "human"
# Normalizamos a dos roles claros para no confundir la lógica ni a la IA.
_SHOPPER_ROLES = {"agent", "bot"}    # NUESTRO cliente incógnito (el que evalúa)
_COMPANY_ROLES = {"user", "human"}   # la EMPRESA evaluada (la que responde)

_ROLE_LABEL = {
    "shopper": "CLIENTE",   # nuestro cliente incógnito
    "company": "EMPRESA",   # la empresa que estamos evaluando
    "unknown": "DESCONOCIDO",
}

# Frases con las que NUESTRO shopper cierra la conversación (detección sin IA)
_FAREWELL_KEYWORDS = [
    "adiós", "adios", "hasta luego", "nos vemos", "que esté bien", "que estes bien",
    "lo voy a pensar", "lo pensaré", "lo pensare", "lo tengo que pensar",
    "no me interesa", "no es para mí", "no es para mi", "no es la opción",
    "no es la opcion", "gracias por tu tiempo", "gracias por la información",
    "gracias por la informacion", "gracias por la honestidad",
]


def _normalize_role(role) -> str:
    """Mapea cualquier rol (agent/bot/user/human) a 'shopper' o 'company'."""
    r = (role or "").strip().lower()
    if r in _SHOPPER_ROLES:
        return "shopper"
    if r in _COMPANY_ROLES:
        return "company"
    return "unknown"


_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
_MODEL = "llama-3.1-8b-instant"

_SYSTEM_PROMPT = """Eres un evaluador de mystery shopping (cliente incógnito).
En la conversación hay dos participantes:
  - CLIENTE  = nuestro cliente incógnito (el comprador potencial que hace preguntas).
  - EMPRESA  = la empresa inmobiliaria que estamos evaluando (la que atiende).

Evalúa ÚNICAMENTE qué tan bien atendió la EMPRESA al CLIENTE.
El quality_score ya tiene penalizaciones por tiempo de respuesta aplicadas — no las recalcules.

Criterios (todos sobre la EMPRESA):
  - responded: ¿la EMPRESA respondió al cliente?
  - gave_price: ¿la EMPRESA dio precio o rango de precio?
  - did_followup: ¿la EMPRESA hizo seguimiento o preguntó para continuar?
  - used_name: ¿la EMPRESA usó el nombre del cliente?
  - attempted_close: ¿la EMPRESA intentó cerrar/agendar (cita, visita, siguiente paso)?

Devuelve ÚNICAMENTE este JSON:
{
  "responded": bool,
  "gave_price": bool,
  "did_followup": bool,
  "used_name": bool,
  "attempted_close": bool,
  "quality_score": int, // IMPORTANTE: Debe ser un número del 0 al 100
  "reasoning": string
}"""


def _build_transcript_text(interaction: dict) -> str:
    """Construye el texto del transcript a partir de call_details o messages."""
    lines = []

    call_details = interaction.get("call_details") or []
    for cd in call_details:
        transcript = parse_transcript(cd.get("transcript"))
        for turn in transcript:
                role = _ROLE_LABEL[_normalize_role(turn.get("role"))]
                msg = (turn.get("message") or "").strip()
                if msg:
                    lines.append(f"[{role}]: {msg}")
        duration = cd.get("duration_sec")
        outcome = cd.get("outcome")
        if outcome:
            lines.append(f"\n[RESULTADO DE LLAMADA: {outcome}, duración: {duration}s]")

    messages = interaction.get("messages") or []
    for msg in sorted(messages, key=lambda m: m.get("sent_at", "")):
        role = _ROLE_LABEL[_normalize_role(msg.get("role"))]
        content = (msg.get("content") or "").strip()
        if content:
            lines.append(f"[{role}]: {content}")

    return "\n".join(lines) if lines else ""


def _build_context_text(interaction: dict) -> str:
    """Construye contexto de campaña para el prompt."""
    parts = []

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
    Calcula tiempos de respuesta en código puro y devuelve (texto_para_prompt, penalización_total, avg_sec).
    La penalización se aplica al quality_score antes de llamar a la IA.
    """
    if not messages:
        return "", 0, None

    sorted_msgs = sorted(messages, key=lambda m: m.get("sent_at", ""))

    # Medimos cuánto tarda la EMPRESA en responderle a NUESTRO shopper:
    # por cada mensaje del shopper, buscamos la siguiente respuesta de la empresa.
    gaps = []
    for i, msg in enumerate(sorted_msgs):
        if _normalize_role(msg.get("role")) != "shopper":
            continue
        ts_sent = _parse_ts(msg.get("sent_at", ""))
        if not ts_sent:
            continue
        for next_msg in sorted_msgs[i + 1:]:
            if _normalize_role(next_msg.get("role")) == "company":
                ts_reply = _parse_ts(next_msg.get("sent_at", ""))
                if ts_reply:
                    gaps.append((ts_reply - ts_sent).total_seconds())
                break

    if not gaps:
        return "", 0, None

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
    return text, total_penalty, avg_sec


def analyze_interaction(interaction_id: str) -> dict:
    """
    Obtiene la interacción completa, la analiza con Groq y guarda el score.
    Devuelve el registro creado en interaction_scores.
    """
    try:
        response = (
            supabase.table("interactions")
            .select("*, campaigns(*, companies(*))")
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
    timing_text, timing_penalty, avg_response_time = _build_timing_context(interaction.get("messages") or [])

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
        "reasoning": result.get("reasoning", ""),
        "scored_by": "ai",
        "reasoning": result.get("reasoning", "")
    }

    saved = supabase.table("interaction_scores").insert(score_data).execute()
    if not saved.data:
        raise HTTPException(status_code=500, detail="No se pudo guardar el score")

    # Marcar interacción como contestada/cerrada y guardar métricas de tiempo
    try:
        now = datetime.utcnow().isoformat() + "Z"
        update_data = {
            "status": "answered",
            "responded_at": now
        }
        if avg_response_time is not None:
            update_data["response_time_sec"] = int(avg_response_time)
            
        supabase.table("interactions").update(update_data).eq("id", interaction_id).execute()
    except Exception as e:
        print(f"Error marcando interacción como answered: {e}")

    return {**saved.data[0], "reasoning": result.get("reasoning", "")}


# ---------------------------------------------------------------------------
# SCORING AUTOMÁTICO (batch)
# ---------------------------------------------------------------------------

def _last_message(messages: list) -> dict | None:
    if not messages:
        return None
    return sorted(messages, key=lambda m: m.get("sent_at", ""))[-1]


def _whatsapp_session_ended(messages: list) -> bool:
    """
    Decide si una conversación de whatsapp ya terminó, SIN usar IA:
      1. Nuestro shopper se despidió (última frase con palabra de cierre), o
      2. Pasaron más de 4h desde el último mensaje (regla de seguridad).
    """
    last = _last_message(messages)
    if not last:
        return False

    # Regla 1: el shopper cerró la conversación
    if _normalize_role(last.get("role")) == "shopper":
        content = (last.get("content") or "").lower()
        if any(kw in content for kw in _FAREWELL_KEYWORDS):
            return True

    # Regla 2: timeout de 4h sin nada nuevo
    ts = _parse_ts(last.get("sent_at", ""))
    if ts:
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age >= _WHATSAPP_TIMEOUT_SEC:
            return True

    return False


def score_pending() -> dict:
    """
    Busca interacciones SIN score y evalúa las que ya estén listas:
      - call:     lista si tiene un call_detail con transcript parseable.
      - whatsapp: lista si la conversación ya terminó (_whatsapp_session_ended).
    Si la empresa nunca respondió, guarda un score 0 SIN gastar IA.
    """
    scored_rows = supabase.table("interaction_scores").select("interaction_id").execute().data or []
    scored_ids = {r["interaction_id"] for r in scored_rows}

    interactions = supabase.table("interactions").select("*").execute().data or []
    results = {"scored": [], "skipped": [], "errors": []}

    for it in interactions:
        iid = it["id"]
        if iid in scored_ids:
            continue

        channel = it.get("channel")

        if channel == "call":
            cds = supabase.table("call_details").select("*").eq("interaction_id", iid).execute().data or []
            has_transcript = any(parse_transcript(cd.get("transcript")) for cd in cds)
            if not has_transcript:
                results["skipped"].append({"id": iid, "reason": "llamada sin transcript aún"})
                continue

        elif channel == "whatsapp":
            msgs = supabase.table("messages").select("*").eq("interaction_id", iid).execute().data or []
            if not _whatsapp_session_ended(msgs):
                results["skipped"].append({"id": iid, "reason": "conversación whatsapp aún activa"})
                continue
            # Sin respuesta de la empresa → score directo sin IA
            if not any(_normalize_role(m.get("role")) == "company" for m in msgs):
                supabase.table("interaction_scores").insert({
                    "interaction_id": iid,
                    "responded": False,
                    "quality_score": 0,
                    "scored_by": "auto",
                }).execute()
                supabase.table("interactions").update({"status": "no_answer"}).eq("id", iid).execute()
                results["scored"].append({"id": iid, "quality_score": 0, "note": "sin respuesta (sin IA)"})
                continue
        else:
            results["skipped"].append({"id": iid, "reason": f"canal no soportado: {channel}"})
            continue

        try:
            score = analyze_interaction(iid)
            supabase.table("interactions").update({"status": "answered"}).eq("id", iid).execute()
            results["scored"].append({"id": iid, "quality_score": score.get("quality_score")})
        except HTTPException as e:
            results["errors"].append({"id": iid, "error": e.detail})
        except Exception as e:
            results["errors"].append({"id": iid, "error": str(e)})

    return results
