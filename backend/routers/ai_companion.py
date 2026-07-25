import json
import base64
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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

@router.websocket("/ws/live-audio")
async def websocket_live_audio(websocket: WebSocket):
    """
    Real-time WebRTC / WebSocket bi-directional audio stream endpoint
    for Gemini 2.5 Flash Native Audio.
    """
    await websocket.accept()
    print("WebRTC / WebSocket Live Audio Client Connected")
    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                payload = json.loads(raw_message)
                transcript = payload.get("transcript", "")
                
                if transcript:
                    req = VoiceInteractionRequest(user_id="user_123", transcript=transcript)
                    ai_resp = orchestrator.process_voice_interaction(req)
                    
                    await websocket.send_json({
                        "type": "ai_response",
                        "agent_name": ai_resp.agent_name,
                        "response_text": ai_resp.response_text,
                        "urgency_level": ai_resp.urgency_level,
                        "suggested_action": ai_resp.suggested_action,
                        "timestamp": ai_resp.timestamp
                    })
            except Exception as parse_err:
                print(f"WebSocket frame processing error: {parse_err}")
    except WebSocketDisconnect:
        print("WebRTC / WebSocket Live Audio Client Disconnected")
