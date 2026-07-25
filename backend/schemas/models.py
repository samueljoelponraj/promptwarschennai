from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserPersona(BaseModel):
    id: str
    name: str
    role: str # "patient", "caregiver", "sponsor", "therapist", "emergency"
    email: str

class VoiceInteractionRequest(BaseModel):
    user_id: str
    transcript: str
    audio_emotion: Optional[str] = "neutral"
    speech_rate_wpm: Optional[int] = 120

class AIResponse(BaseModel):
    agent_name: str
    response_text: str
    suggested_action: str
    urgency_level: str # "SAFE", "ELEVATED_STRESS", "HIGH_CRAVING", "ACUTE_CRISIS"
    timestamp: str

class EmergencySOSRequest(BaseModel):
    user_id: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    trigger_reason: str
    audio_snippet: Optional[str] = None

class EmergencySOSResponse(BaseModel):
    sos_id: str
    status: str # "DISPATCHED", "ALERTED_CAREGIVERS", "ESCALATED"
    safety_message: str
    contacts_notified: List[str]
    timestamp: str

class RecoveryStreak(BaseModel):
    user_id: str
    days_sober: int
    current_streak_start: str
    triggers_log_count: int
    mood_score_avg: float # 1.0 to 10.0

class CaregiverAlert(BaseModel):
    id: str
    patient_name: str
    severity: str
    message: str
    created_at: str
    is_resolved: bool = False
