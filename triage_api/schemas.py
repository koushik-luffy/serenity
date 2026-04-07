from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


Role = Literal["user", "assistant", "system", "counselor"]


class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=4000)


class SessionRecord(BaseModel):
    session_id: str
    final_severity: str
    subtype: str
    emergency_flag: bool = False
    days_ago: int | None = None
    notes: str | None = None


class AnalyzeRequest(BaseModel):
    session_id: str
    user_id: str | None = None
    recent_messages: list[Message] = Field(min_length=1, max_length=16)
    prior_summary: str | None = None


class PredictionPayload(BaseModel):
    severity: Literal["low", "medium", "high_crisis"]
    subtype: Literal[
        "suicidal_ideation",
        "self_harm",
        "panic_anxiety",
        "depression_hopelessness",
        "abuse_violence",
        "substance_overdose",
        "accident_injury",
        "general_distress",
    ]
    emergency_flag: bool
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class EmergencyContactInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    relationship: str = Field(min_length=1, max_length=80)
    phone_number: str | None = Field(default=None, min_length=7, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    preferred_channel: Literal["sms", "email"] = "sms"
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def validate_contact_method(self) -> "EmergencyContactInput":
        if not self.phone_number and not self.email:
            raise ValueError("Either phone_number or email must be provided.")
        if self.preferred_channel == "sms" and not self.phone_number:
            raise ValueError("preferred_channel='sms' requires phone_number.")
        if self.preferred_channel == "email" and not self.email:
            raise ValueError("preferred_channel='email' requires email.")
        return self


class EmergencyContact(EmergencyContactInput):
    contact_id: str
    created_at: str


class EmergencyContactsUpsertRequest(BaseModel):
    user_id: str
    contacts: list[EmergencyContactInput] = Field(min_length=1, max_length=5)


class EmergencyContactsResponse(BaseModel):
    user_id: str
    contacts: list[EmergencyContact] = Field(default_factory=list)


class QueueActionRequest(BaseModel):
    action: Literal["prioritize", "start_outreach", "resolve"]
    note: str | None = Field(default=None, max_length=240)


class AlertDelivery(BaseModel):
    contact_id: str
    contact_name: str
    channel: Literal["sms", "email"]
    target: str
    status: Literal["simulated", "skipped"]
    reason: str | None = None


class EmergencyAlertResult(BaseModel):
    triggered: bool
    alert_id: str | None = None
    user_id: str
    session_id: str
    threshold: str
    status: Literal["not_triggered", "no_contacts", "simulated"]
    deliveries: list[AlertDelivery] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    session_id: str
    user_id: str
    severity: Literal["low", "medium", "high_crisis"]
    subtype: Literal[
        "suicidal_ideation",
        "self_harm",
        "panic_anxiety",
        "depression_hopelessness",
        "abuse_violence",
        "substance_overdose",
        "accident_injury",
        "general_distress",
    ]
    emergency_flag: bool
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    top_indicators: list[str] = Field(default_factory=list, max_length=4)
    safe_fail_escalated: bool = False
    neural_prediction: PredictionPayload
    final_prediction: PredictionPayload
    emergency_alert: EmergencyAlertResult


class SummaryRequest(BaseModel):
    sessions: list[SessionRecord] = Field(default_factory=list, max_length=50)


class SummaryResponse(BaseModel):
    prior_summary: str


class ChatContext(BaseModel):
    severity: Literal["low", "medium", "high_crisis"]
    subtype: Literal[
        "suicidal_ideation",
        "self_harm",
        "panic_anxiety",
        "depression_hopelessness",
        "abuse_violence",
        "substance_overdose",
        "accident_injury",
        "general_distress",
    ]
    emergency_flag: bool
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    top_indicators: list[str] = Field(default_factory=list, max_length=6)


class ChatRequest(BaseModel):
    session_id: str
    user_id: str | None = None
    recent_messages: list[Message] = Field(min_length=1, max_length=20)
    prior_summary: str | None = None
    triage_context: ChatContext | None = None
    include_audio: bool = False


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    reply: str
    model: str
    audio_wav_base64: str | None = None
    fallback_used: bool = False
    notice: str | None = None
