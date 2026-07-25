from datetime import datetime
from backend.ai.safety_guard import SafetyGuard
from backend.schemas.models import VoiceInteractionRequest, AIResponse

class AgentOrchestrator:
    """
    Multi-Agent Orchestration Layer executing clinical Motivational Interviewing,
    Craving De-escalation, and Emergency Crisis Safeguards.
    """
    def __init__(self):
        self.safety_guard = SafetyGuard()

    def process_voice_interaction(self, request: VoiceInteractionRequest) -> AIResponse:
        # Step 1: Safety & Urgency Evaluation
        safety_eval = self.safety_guard.evaluate_input_safety(request.transcript)
        urgency_level = safety_eval["level"]
        
        # Step 2: Route to appropriate Specialized Agent
        if urgency_level == "ACUTE_CRISIS":
            return self._emergency_sentinel_agent(request)
        elif urgency_level == "HIGH_CRAVING":
            return self._craving_assistant_agent(request)
        else:
            return self._motivational_companion_agent(request)

    def _emergency_sentinel_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        raw_text = (
            "I hear how much pain you're in, and your safety is the absolute top priority. "
            "You are not alone right now. I am triggering an emergency notification to your designated sponsor and caregiver, "
            "and staying right here with you. Please take a deep breath with me."
        )
        sanitized = self.safety_guard.sanitize_output(raw_text)
        return AIResponse(
            agent_name="Emergency SOS Sentinel Agent",
            response_text=sanitized,
            suggested_action="TRIGGER_EMERGENCY_SOS",
            urgency_level="ACUTE_CRISIS",
            timestamp=datetime.utcnow().isoformat()
        )

    def _craving_assistant_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        raw_text = (
            "Thank you for sharing that with me. It takes tremendous courage to speak up when an urge hits. "
            "A craving is like a wave—it rises, peaks, and will pass. Let's do a 4-7-8 breathing exercise together right now. "
            "Inhale through your nose for 4 seconds..."
        )
        sanitized = self.safety_guard.sanitize_output(raw_text)
        return AIResponse(
            agent_name="Craving De-escalation Agent",
            response_text=sanitized,
            suggested_action="START_BREATHING_EXERCISE",
            urgency_level="HIGH_CRAVING",
            timestamp=datetime.utcnow().isoformat()
        )

    def _motivational_companion_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        raw_text = (
            f"I hear you. You mentioned '{request.transcript}'. Reflecting on your progress over the past days, "
            "you've built solid resilience. What is one small thing you can do right now to treat yourself with kindness today?"
        )
        sanitized = self.safety_guard.sanitize_output(raw_text)
        return AIResponse(
            agent_name="Motivational Interviewing Companion Agent",
            response_text=sanitized,
            suggested_action="OPEN_DAILY_JOURNAL",
            urgency_level="SAFE",
            timestamp=datetime.utcnow().isoformat()
        )
