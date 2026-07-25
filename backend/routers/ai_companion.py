from fastapi import APIRouter, HTTPException
from backend.schemas.models import VoiceInteractionRequest, AIResponse
from backend.ai.agent_orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/v1/ai", tags=["AI Companion"])
orchestrator = AgentOrchestrator()

@router.post("/voice-interact", response_model=AIResponse)
def process_voice(request: VoiceInteractionRequest):
    """
    Process zero-typing voice transcript input and route to the multi-agent AI system.
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
    
    return orchestrator.process_voice_interaction(request)
