from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

# --- RESPUESTAS ESTÁNDAR ---
class SuccessResponse(BaseModel):
    success: bool = True
    status_code: int
    data: Any

class ErrorResponse(BaseModel):
    success: bool = False
    status_code: int
    error: str

# --- COMPANIES ---
class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None

class CompanyResponse(CompanyCreate):
    id: UUID
    created_at: datetime

# --- PERSONAS ---
class PersonaCreate(BaseModel):
    name: str
    fake_company: Optional[str] = None
    role: Optional[str] = None
    voice_id: Optional[str] = None
    script_template: Optional[str] = None
    channel: Optional[str] = None

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    fake_company: Optional[str] = None
    role: Optional[str] = None
    voice_id: Optional[str] = None
    script_template: Optional[str] = None
    channel: Optional[str] = None

class PersonaResponse(PersonaCreate):
    id: UUID
    created_at: datetime

# --- CAMPAIGNS ---
class CampaignCreate(BaseModel):
    company_id: UUID
    name: str
    status: Optional[str] = "paused"
    channels: Optional[List[str]] = []
    frequency_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    channels: Optional[List[str]] = None
    frequency_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class CampaignResponse(CampaignCreate):
    id: UUID
    created_at: datetime

# --- INTERACTIONS ---
class InteractionCreate(BaseModel):
    campaign_id: UUID
    persona_id: Optional[UUID] = None
    channel: Optional[str] = None
    status: Optional[str] = "sent"
    external_id: Optional[str] = None

class InteractionUpdate(BaseModel):
    persona_id: Optional[UUID] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    external_id: Optional[str] = None
    responded_at: Optional[datetime] = None
    response_time_sec: Optional[int] = None

class InteractionResponse(InteractionCreate):
    id: UUID
    initiated_at: datetime
    responded_at: Optional[datetime] = None
    response_time_sec: Optional[int] = None

# --- CALL DETAILS ---
class CallDetailCreate(BaseModel):
    interaction_id: Optional[UUID] = None
    elevenlabs_agent_id: Optional[str] = None
    elevenlabs_conv_id: Optional[str] = None
    twilio_call_sid: Optional[str] = None
    duration_sec: Optional[int] = None
    transcript: Optional[Any] = None   # puede llegar como list, str o dict
    recording_url: Optional[str] = None
    outcome: Optional[str] = None

class CallDetailUpdate(BaseModel):
    elevenlabs_agent_id: Optional[str] = None
    elevenlabs_conv_id: Optional[str] = None
    twilio_call_sid: Optional[str] = None
    duration_sec: Optional[int] = None
    transcript: Optional[Dict[str, Any]] = None
    recording_url: Optional[str] = None
    outcome: Optional[str] = None

class CallDetailResponse(CallDetailCreate):
    id: UUID

# --- MESSAGES ---
class MessageCreate(BaseModel):
    interaction_id: UUID
    role: str
    content: str
    channel: Optional[str] = None
    external_msg_id: Optional[str] = None

class MessageResponse(MessageCreate):
    id: UUID
    sent_at: datetime

# --- INTERACTION SCORES ---
class InteractionScoreCreate(BaseModel):
    interaction_id: UUID
    responded: Optional[bool] = False
    gave_price: Optional[bool] = False
    did_followup: Optional[bool] = False
    used_name: Optional[bool] = False
    attempted_close: Optional[bool] = False
    quality_score: Optional[int] = None
    scored_by: Optional[str] = None

class InteractionScoreUpdate(BaseModel):
    responded: Optional[bool] = None
    gave_price: Optional[bool] = None
    did_followup: Optional[bool] = None
    used_name: Optional[bool] = None
    attempted_close: Optional[bool] = None
    quality_score: Optional[int] = None
    scored_by: Optional[str] = None

class InteractionScoreResponse(InteractionScoreCreate):
    id: UUID

# --- REPORTS ---
class ReportCreate(BaseModel):
    campaign_id: UUID
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    metrics: Optional[Dict[str, Any]] = None
    findings: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    status: Optional[str] = "draft"

class ReportResponse(ReportCreate):
    id: UUID
    generated_at: datetime
