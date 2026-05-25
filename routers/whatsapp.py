from fastapi import APIRouter, Request, BackgroundTasks, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.whatsapp_agent import responder, iniciar_auditoria, PRIMER_MENSAJE
from services.audit_orchestrator import prepare_audit
import logging

logger = logging.getLogger("whatsapp_router")
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Agent"])

class IniciarRequest(BaseModel):
    phone: str                          # Número del vendedor a auditar
    company_name: Optional[str] = None  # Nombre de la empresa (opcional)

@router.post("/webhook")
async def twilio_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe mensajes entrantes de Twilio.
    Responde 200 inmediatamente y procesa el mensaje en background.
    """
    form_data = await request.form()
    
    from_phone = form_data.get("From")
    body = form_data.get("Body")
    message_sid = form_data.get("MessageSid")

    logger.info(f"📬 Webhook recibido de: {from_phone} - SID: {message_sid}")

    if from_phone and body:
        background_tasks.add_task(responder, from_phone, body, message_sid)

    # Twilio requiere una respuesta 200 rápida para evitar timeouts
    return "OK"

@router.post("/iniciar", status_code=202)
async def iniciar_auditoria_endpoint(payload: IniciarRequest, background_tasks: BackgroundTasks):
    """
    Dispara una nueva auditoría de mystery shopping por WhatsApp.
    
    Crea automáticamente todos los registros necesarios en Supabase
    (empresa, persona, campaña, interacción) y envía el primer mensaje.
    """
    if not payload.phone:
        raise HTTPException(status_code=400, detail="phone es requerido")

    phone_norm = payload.phone if payload.phone.startswith("whatsapp:") else f"whatsapp:{payload.phone}"
    
    # Preparar todos los registros en Supabase
    try:
        audit_data = prepare_audit(phone_norm, payload.company_name)
        interaction_id = audit_data["interaction_id"]
    except Exception as e:
        logger.error(f"❌ Error preparando auditoría: {e}")
        raise HTTPException(status_code=500, detail=f"Error preparando auditoría en base de datos: {str(e)}")

    logger.info(f"🚀 Auditoría lista para {phone_norm} (interaction: {interaction_id})")
    
    # Procesar en background para devolver respuesta rápida
    background_tasks.add_task(iniciar_auditoria, phone_norm, interaction_id)
    
    return {
        "message": "Auditoría iniciada",
        "phone": phone_norm,
        "interaction_id": interaction_id,
        "company_name": audit_data["company_name"],
        "campaign_id": audit_data["campaign_id"],
        "primer_mensaje": PRIMER_MENSAJE
    }

