"""
Orquestador de auditorías.

Se encarga de crear/buscar todos los registros necesarios en Supabase
(company, persona, campaign, interaction) antes de iniciar una
conversación de WhatsApp, garantizando que no haya violaciones de FK.
"""

import logging
from datetime import datetime, date
from db import supabase

logger = logging.getLogger("audit_orchestrator")
logger.setLevel(logging.INFO)



def get_or_create_company(phone: str, company_name: str | None = None) -> dict:
    """Busca una empresa por su whatsapp_number. Si no existe, la crea."""
    # Normalizar el teléfono (quitar prefijo whatsapp: si existe)
    clean_phone = phone.replace("whatsapp:", "").strip()

    try:
        response = (
            supabase.table("companies")
            .select("*")
            .eq("whatsapp_number", clean_phone)
            .limit(1)
            .execute()
        )
        if response.data:
            logger.info(f"✅ Empresa encontrada: {response.data[0]['id']} ({response.data[0]['name']})")
            return response.data[0]

        # Crear empresa
        new_company = {
            "name": company_name or f"Empresa {clean_phone}",
            "whatsapp_number": clean_phone,
            "industry": "inmobiliaria",
        }
        created = supabase.table("companies").insert(new_company).execute()
        logger.info(f"🆕 Empresa creada: {created.data[0]['id']} ({created.data[0]['name']})")
        return created.data[0]
    except Exception as e:
        logger.error(f"❌ Error en get_or_create_company: {e}")
        raise


def get_or_create_campaign(company_id: str) -> dict:
    """Busca una campaña activa de WhatsApp para la empresa. Si no existe, la crea."""
    try:
        response = (
            supabase.table("campaigns")
            .select("*")
            .eq("company_id", company_id)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        if response.data:
            # Verificar que incluya whatsapp en sus canales
            campaign = response.data[0]
            channels = campaign.get("channels") or []
            if "whatsapp" in channels:
                logger.info(f"✅ Campaña encontrada: {campaign['id']} ({campaign['name']})")
                return campaign

        # Crear campaña
        new_campaign = {
            "company_id": company_id,
            "name": "Auditoría WhatsApp",
            "status": "active",
            "channels": ["whatsapp"],
            "start_date": date.today().isoformat(),
        }
        created = supabase.table("campaigns").insert(new_campaign).execute()
        logger.info(f"🆕 Campaña creada: {created.data[0]['id']}")
        return created.data[0]
    except Exception as e:
        logger.error(f"❌ Error en get_or_create_campaign: {e}")
        raise


def create_interaction(campaign_id: str, phone: str) -> dict:
    """Crea un nuevo registro de interacción en Supabase."""
    clean_phone = phone.replace("whatsapp:", "").strip()

    try:
        new_interaction = {
            "campaign_id": campaign_id,
            "channel": "whatsapp",
            "status": "sent",
            "external_id": clean_phone,
        }
        created = supabase.table("interactions").insert(new_interaction).execute()
        logger.info(f"🆕 Interacción creada: {created.data[0]['id']}")
        return created.data[0]
    except Exception as e:
        logger.error(f"❌ Error en create_interaction: {e}")
        raise


def prepare_audit(phone: str, company_name: str | None = None) -> dict:
    """
    Orquestador principal. Prepara todos los registros necesarios en Supabase
    y devuelve un dict con los IDs creados/encontrados.

    Returns:
        {
            "interaction_id": str,
            "campaign_id": str,
            "company_id": str,
            "persona_id": str,
            "company_name": str,
        }
    """
    logger.info(f"🔧 Preparando auditoría para {phone}...")

    # 2. Empresa (por número de WhatsApp del vendedor)
    company = get_or_create_company(phone, company_name)

    # 3. Campaña activa para esa empresa
    campaign = get_or_create_campaign(company["id"])

    # 4. Interacción nueva
    interaction = create_interaction(campaign["id"], phone)

    result = {
        "interaction_id": interaction["id"],
        "campaign_id": campaign["id"],
        "company_id": company["id"],
        "company_name": company["name"],
    }

    logger.info(f"✅ Auditoría preparada: interaction_id={result['interaction_id']}")
    return result
