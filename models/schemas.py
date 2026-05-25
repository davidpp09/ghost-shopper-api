from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from uuid import UUID
import re

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
    name: str = Field(..., min_length=1, max_length=100)
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None

    @field_validator("industry", "city", mode="before")
    @classmethod
    def no_empty_string(cls, v):
        if v is not None and str(v).strip() == "":
            return None
        return v

    @field_validator("phone", "whatsapp_number", mode="before")
    @classmethod
    def valid_phone(cls, v):
        if v is None:
            return v
        if not re.match(r"^[\d\s\+\-\(\)]+$", v):
            raise ValueError("Solo se permiten números, +, -, espacios y paréntesis")
        return v

    @field_validator("website", mode="before")
    @classmethod
    def valid_url(cls, v):
        if v is None:
            return v
        if not re.match(r"^https?://", v):
            raise ValueError("La URL debe comenzar con http:// o https://")
        return v

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[EmailStr] = None
    city: Optional[str] = None

    @field_validator("industry", "city", mode="before")
    @classmethod
    def no_empty_string(cls, v):
        if v is not None and str(v).strip() == "":
            return None
        return v

    @field_validator("phone", "whatsapp_number", mode="before")
    @classmethod
    def valid_phone(cls, v):
        if v is None:
            return v
        if not re.match(r"^[\d\s\+\-\(\)]+$", v):
            raise ValueError("Solo se permiten números, +, -, espacios y paréntesis")
        return v

    @field_validator("website", mode="before")
    @classmethod
    def valid_url(cls, v):
        if v is None:
            return v
        if not re.match(r"^https?://", v):
            raise ValueError("La URL debe comenzar con http:// o https://")
        return v

class CompanyResponse(CompanyCreate):
    id: UUID
    created_at: datetime

# --- CAMPAIGNS ---
class CampaignCreate(BaseModel):
    company_id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    status: Optional[Literal["active", "paused", "done"]] = "paused"
    channels: Optional[List[Literal["call", "whatsapp", "email"]]] = []
    frequency_days: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def end_after_start(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date debe ser posterior a start_date")
        return self

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    status: Optional[Literal["active", "paused", "done"]] = None
    channels: Optional[List[Literal["call", "whatsapp", "email"]]] = None
    frequency_days: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def end_after_start(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date debe ser posterior a start_date")
        return self

class CampaignResponse(CampaignCreate):
    id: UUID
    created_at: datetime

# --- INTERACTIONS ---
class InteractionCreate(BaseModel):
    campaign_id: UUID
    channel: Optional[Literal["call", "whatsapp", "email"]] = None
    status: Optional[Literal["sent", "answered", "no_answer"]] = "sent"
    external_id: Optional[str] = None

class InteractionUpdate(BaseModel):
    channel: Optional[Literal["call", "whatsapp", "email"]] = None
    status: Optional[Literal["sent", "answered", "no_answer"]] = None
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
    duration_sec: Optional[int] = Field(None, ge=0)
    transcript: Optional[Any] = None
    recording_url: Optional[str] = None
    outcome: Optional[Literal["answered", "no_answer", "busy", "failed"]] = None

class CallDetailUpdate(BaseModel):
    elevenlabs_agent_id: Optional[str] = None
    elevenlabs_conv_id: Optional[str] = None
    twilio_call_sid: Optional[str] = None
    duration_sec: Optional[int] = Field(None, ge=0)
    transcript: Optional[Any] = None
    recording_url: Optional[str] = None
    outcome: Optional[Literal["answered", "no_answer", "busy", "failed"]] = None

class CallDetailResponse(CallDetailCreate):
    id: UUID

# --- MESSAGES ---
class MessageCreate(BaseModel):
    interaction_id: UUID
    role: Literal["agent", "user"]
    content: str = Field(..., min_length=1)
    channel: Optional[Literal["call", "whatsapp", "email"]] = None
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
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    reasoning: Optional[str] = None
    scored_by: Optional[str] = None

class InteractionScoreUpdate(BaseModel):
    responded: Optional[bool] = None
    gave_price: Optional[bool] = None
    did_followup: Optional[bool] = None
    used_name: Optional[bool] = None
    attempted_close: Optional[bool] = None
    quality_score: Optional[int] = Field(None, ge=0, le=100)
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
    status: Optional[Literal["draft", "sent"]] = "draft"

    @model_validator(mode="after")
    def end_after_start(self):
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end debe ser igual o posterior a period_start")
        return self

class ReportResponse(ReportCreate):
    id: UUID
    generated_at: datetime
