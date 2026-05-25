import os
import json
from datetime import datetime
from groq import Groq
import services.companies as company_svc
import services.campaigns as campaign_svc
import services.interactions as interaction_svc
import services.calls as calls_svc

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
_MODEL = "llama-3.1-8b-instant"


def _generic_name() -> str:
    return f"Empresa-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def _parse_company_from_context(context: str) -> dict:
    """
    Usa Groq para extraer datos de empresa del texto libre.
    Devuelve un dict con las claves que pudo detectar.
    Si falla o no hay context, devuelve {}.
    """
    if not context or not context.strip():
        return {}

    prompt = (
        "Extrae datos de una empresa del siguiente texto. "
        "Devuelve SOLO un JSON con estas claves (pon null si no se menciona):\n"
        "  name     → nombre de la empresa\n"
        "  industry → giro o sector\n"
        "  city     → ciudad\n"
        "  website  → URL del sitio web\n\n"
        f"Texto: {context}"
    )

    try:
        resp = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=200,
            temperature=0,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {}


def launch_bot_call(phone: str, context: str = "") -> dict:
    """
    Flujo completo de un click:
      1. Groq parsea el context y extrae datos de la empresa
      2. Crea la empresa en DB
      3. Crea una campaña activa (call + whatsapp)
      4. Crea una interacción tipo call
      5. Dispara la llamada vía ElevenLabs → ring ring
    """
    # 1. Extraer datos de empresa del contexto con IA
    extracted = _parse_company_from_context(context)

    # 2. Armar y crear empresa
    company_data = {
        "name": extracted.get("name") or _generic_name(),
        "phone": phone,
    }
    if extracted.get("industry"):
        company_data["industry"] = extracted["industry"]
    if extracted.get("city"):
        company_data["city"] = extracted["city"]
    if extracted.get("website"):
        company_data["website"] = extracted["website"]

    company = company_svc.create(company_data)
    company_id = company["id"]

    # 3. Crear campaña
    campaign = campaign_svc.create({
        "company_id": company_id,
        "name": f"Campaña - {company_data['name']}",
        "channels": ["call", "whatsapp"],
        "status": "active",
    })
    campaign_id = campaign["id"]

    # 4. Crear interacción
    interaction = interaction_svc.create({
        "campaign_id": campaign_id,
        "channel": "call",
        "status": "sent",
    })
    interaction_id = interaction["id"]

    # 5. Disparar llamada
    call_result = calls_svc.initiate_call(interaction_id)

    return {
        "company_id": company_id,
        "company_name": company_data["name"],
        "campaign_id": campaign_id,
        "interaction_id": interaction_id,
        "conversation_id": call_result.get("conversation_id"),
        "status": "calling",
        "to_number": phone,
    }
