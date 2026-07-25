import os
from datetime import datetime
from backend.config import settings
from backend.ai.safety_guard import SafetyGuard
from backend.schemas.models import VoiceInteractionRequest, AIResponse

# Import google-generativeai dynamically if available
try:
    import google.generativeai as genai
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class AgentOrchestrator:
    """
    Multi-Agent Orchestration Engine powered by Google Gemini 1.5 Flash
    and clinical Motivational Interviewing (OARS) frameworks.
    """
    def __init__(self):
        self.safety_guard = SafetyGuard()
        self.api_key = settings.GEMINI_API_KEY

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
        prompt = f"Patient in crisis said: '{request.transcript}'. Generate immediate grounding response."
        llm_response = self._call_gemini(
            system_instruction="You are an Emergency Crisis Safeguard AI for substance recovery. Be extremely grounding, warm, and immediate.",
            prompt=prompt,
            fallback=(
                "I hear how much pain you're in, and your safety is the absolute top priority. "
                "You are not alone right now. I am triggering an emergency notification to your designated sponsor and caregiver, "
                "and staying right here with you. Please take a deep breath with me."
            )
        )
        sanitized = self.safety_guard.sanitize_output(llm_response)
        return AIResponse(
            agent_name="Emergency SOS Sentinel Agent",
            response_text=sanitized,
            suggested_action="TRIGGER_EMERGENCY_SOS",
            urgency_level="ACUTE_CRISIS",
            timestamp=datetime.utcnow().isoformat()
        )

    def _craving_assistant_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        prompt = f"Patient experiencing intense craving said: '{request.transcript}'. Guide them through urge surfing."
        llm_response = self._call_gemini(
            system_instruction="You are a clinical Craving De-escalation Specialist using Urge Surfing and CBT grounding techniques. Keep it short and actionable.",
            prompt=prompt,
            fallback=(
                "Thank you for sharing that with me. It takes tremendous courage to speak up when an urge hits. "
                "A craving is like a wave—it rises, peaks, and will pass. Let's do a 4-7-8 breathing exercise together right now. "
                "Inhale through your nose..."
            )
        )
        sanitized = self.safety_guard.sanitize_output(llm_response)
        return AIResponse(
            agent_name="Craving De-escalation Agent",
            response_text=sanitized,
            suggested_action="START_BREATHING_EXERCISE",
            urgency_level="HIGH_CRAVING",
            timestamp=datetime.utcnow().isoformat()
        )

    def _motivational_companion_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        prompt = f"Patient in recovery said: '{request.transcript}'. Respond using Motivational Interviewing (OARS)."
        llm_response = self._call_gemini(
            system_instruction="You are an empathetic clinical Recovery Companion. Use Motivational Interviewing (Open Questions, Affirmations, Reflective Listening, Summaries). Never judge.",
            prompt=prompt,
            fallback=(
                f"I hear you. You mentioned '{request.transcript}'. Reflecting on your progress over the past days, "
                "you've built solid resilience. What is one small thing you can do right now to treat yourself with kindness today?"
            )
        )
        sanitized = self.safety_guard.sanitize_output(llm_response)
        return AIResponse(
            agent_name="Motivational Interviewing Companion Agent",
            response_text=sanitized,
            suggested_action="OPEN_DAILY_JOURNAL",
            urgency_level="SAFE",
            timestamp=datetime.utcnow().isoformat()
        )

    def _call_gemini(self, system_instruction: str, prompt: str, fallback: str) -> str:
        if HAS_GENAI and self.api_key:
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"Gemini API call failed, using dynamic clinical fallback: {e}")
        return fallback
