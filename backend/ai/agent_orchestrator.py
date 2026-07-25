import os
from datetime import datetime
from backend.config import settings
from backend.ai.safety_guard import SafetyGuard
from backend.schemas.models import VoiceInteractionRequest, AIResponse

# Attempt 1: Import Native GCP Vertex AI SDK
HAS_VERTEX_AI = False
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    project_id = settings.GCP_PROJECT
    location = settings.GCP_LOCATION
    vertexai.init(project=project_id, location=location)
    HAS_VERTEX_AI = True
    print(f"Vertex AI SDK initialized for project '{project_id}' in region '{location}'")
except Exception as e:
    print(f"Vertex AI initialization notice: {e}")

# Attempt 2: Fallback to google-generativeai API Key
HAS_GENAI = False
try:
    import google.generativeai as genai
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        HAS_GENAI = True
except Exception as e:
    print(f"GenAI notice: {e}")


class AgentOrchestrator:
    """
    Multi-Agent Orchestration Engine powered by Google Cloud Vertex AI (Gemini 1.5 Flash / Pro).
    Generates dynamic clinical Motivational Interviewing, Craving De-escalation, and Emergency SOS responses.
    """
    def __init__(self):
        self.safety_guard = SafetyGuard()
        # Official production model endpoints for Vertex AI & Gemini APIs
        self.model_candidates = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ]

    def process_voice_interaction(self, request: VoiceInteractionRequest) -> AIResponse:
        # Step 1: Safety & Urgency Interception
        safety_eval = self.safety_guard.evaluate_input_safety(request.transcript)
        urgency_level = safety_eval["level"]
        
        if urgency_level == "ACUTE_CRISIS":
            return self._emergency_sentinel_agent(request)
        elif urgency_level == "HIGH_CRAVING":
            return self._craving_assistant_agent(request)
        else:
            return self._motivational_companion_agent(request)

    def _emergency_sentinel_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        system_instruction = (
            "You are an Emergency Crisis Safeguard AI for substance recovery. "
            "The user is in acute distress or crisis. Respond with immediate warmth, grounding, and crisis support. "
            "Keep your response concise, empathetic, and spoken directly to the person."
        )
        llm_response = self._generate_live_response(
            system_instruction=system_instruction,
            user_transcript=request.transcript,
            default_fallback=(
                "I hear how much pain you're in, and your safety is the absolute top priority. "
                "You are not alone right now. I am triggering an emergency notification to your designated sponsor and caregiver, "
                "and staying right here with you. Please take a deep breath with me."
            )
        )
        sanitized = self.safety_guard.sanitize_output(llm_response)
        
        return AIResponse(
            agent_name="Emergency SOS Sentinel Agent (Vertex AI Gemini)",
            response_text=sanitized,
            suggested_action="TRIGGER_EMERGENCY_SOS",
            urgency_level="ACUTE_CRISIS",
            timestamp=datetime.utcnow().isoformat()
        )

    def _craving_assistant_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        system_instruction = (
            "You are a clinical Craving De-escalation Specialist using CBT and Urge Surfing principles. "
            "A patient experiencing an intense craving needs short, empowering, and actionable grounding guidance right now. "
            "Speak directly to them in an encouraging, calm voice."
        )
        llm_response = self._generate_live_response(
            system_instruction=system_instruction,
            user_transcript=request.transcript,
            default_fallback=(
                "Thank you for sharing that with me. It takes tremendous courage to speak up when an urge hits. "
                "A craving is like a wave—it rises, peaks, and will pass. Let's do a 4-7-8 breathing exercise together right now."
            )
        )
        sanitized = self.safety_guard.sanitize_output(llm_response)
        
        return AIResponse(
            agent_name="Craving De-escalation Agent (Vertex AI Gemini)",
            response_text=sanitized,
            suggested_action="START_BREATHING_EXERCISE",
            urgency_level="HIGH_CRAVING",
            timestamp=datetime.utcnow().isoformat()
        )

    def _motivational_companion_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        system_instruction = (
            "You are an empathetic clinical Recovery Companion powered by Google Cloud Vertex AI. "
            "Use Motivational Interviewing principles (Open Questions, Affirmations, Reflective Listening, Summaries). "
            "Never judge or lecture. Speak warmly and authentically to support their recovery journey."
        )
        llm_response = self._generate_live_response(
            system_instruction=system_instruction,
            user_transcript=request.transcript,
            default_fallback=(
                f"I hear you. Thank you for sharing '{request.transcript}'. Reflecting on your progress, "
                "you've built solid resilience. What is one small positive goal you can focus on today?"
            )
        )
        sanitized = self.safety_guard.sanitize_output(llm_response)
        
        return AIResponse(
            agent_name="Motivational Companion Agent (Vertex AI Gemini)",
            response_text=sanitized,
            suggested_action="OPEN_DAILY_JOURNAL",
            urgency_level="SAFE",
            timestamp=datetime.utcnow().isoformat()
        )

    def _generate_live_response(self, system_instruction: str, user_transcript: str, default_fallback: str) -> str:
        prompt = f"Patient said: '{user_transcript}'. Please respond directly to them in 2-3 empathetic sentences."

        # Priority 1: Native GCP Vertex AI (Serves natively on Cloud Run)
        if HAS_VERTEX_AI:
            for model_name in self.model_candidates:
                try:
                    model = GenerativeModel(
                        model_name=model_name,
                        system_instruction=[system_instruction]
                    )
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    print(f"[Vertex AI Error] Model '{model_name}' failed: {e}")

        # Priority 2: Google Generative AI Developer API Key
        if HAS_GENAI and settings.GEMINI_API_KEY:
            for model_name in self.model_candidates:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    print(f"[GenAI Error] Model '{model_name}' failed: {e}")

        # Warm clinical fallback if API calls fail
        return default_fallback
