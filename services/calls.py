import os
from fastapi import HTTPException
from elevenlabs import ElevenLabs
from elevenlabs.types import ConversationInitiationClientDataRequestInput
from db import supabase

_ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
_ELEVENLABS_AGENT_ID = os.environ.get("ELEVENLABS_AGENT_ID", "")
_ELEVENLABS_PHONE_ID = os.environ.get("ELEVENLABS_PHONE_NUMBER_ID", "")


def initiate_call(interaction_id: str) -> dict:
    """
    Inicia una llamada outbound via ElevenLabs usando el cliente oficial de Python.
    Pasa el interaction_id como dynamic_variable para que el agente lo tenga disponible
    y Make lo reciba en el webhook post-call.
    """
    if not _ELEVENLABS_API_KEY or not _ELEVENLABS_AGENT_ID or not _ELEVENLABS_PHONE_ID:
        raise HTTPException(
            status_code=500,
            detail="Faltan variables de entorno de ElevenLabs",
        )

    interaction_resp = (
        supabase.table("interactions")
        .select("*, campaigns(*, companies(*))")
        .eq("id", interaction_id)
        .execute()
    )
    if not interaction_resp.data:
        raise HTTPException(status_code=404, detail="Interaction not found")

    interaction = interaction_resp.data[0]
    campaign    = interaction.get("campaigns") or {}
    company     = campaign.get("companies") or {}

    phone = company.get("phone")
    if not phone:
        raise HTTPException(
            status_code=422,
            detail="La empresa no tiene número de teléfono registrado",
        )

    client = ElevenLabs(api_key=_ELEVENLABS_API_KEY)

    response = client.conversational_ai.twilio.outbound_call(
        agent_id=_ELEVENLABS_AGENT_ID,
        agent_phone_number_id=_ELEVENLABS_PHONE_ID,
        to_number=phone,
        conversation_initiation_client_data=ConversationInitiationClientDataRequestInput(
            dynamic_variables={
                "interaction_id": interaction_id,
                "campaign_id": str(campaign.get("id", "")),
                "campaign_name": campaign.get("name", ""),
                "company_name": company.get("name", ""),
            }
        ),
    )

    conversation_id = response.conversation_id

    supabase.table("interactions").update(
        {"external_id": conversation_id}
    ).eq("id", interaction_id).execute()

    return {
        "interaction_id": interaction_id,
        "conversation_id": conversation_id,
        "status": "calling",
        "to_number": phone,
    }
