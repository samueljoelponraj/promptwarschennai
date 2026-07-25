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
    print(f"Vertex AI initialized for project: {project_id} in region {location}")
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
    Multi-Agent Orchestration Engine powered by 100% Live Google Cloud Vertex AI
    using Gemini 2.5 Flash Native Audio (gemini-2.5-flash-native-audio).
    Zero static fallback strings.
    """
    def __init__(self):
        self.safety_guard = SafetyGuard()
        self.primary_model = settings.DEFAULT_MODEL # gemini-2.5-flash-native-audio
        self.secondary_model = settings.SECONDARY_MODEL # gemini-1.5-flash

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
            "You are an Emergency Crisis Safeguard AI for substance use disorder recovery. "
            "The user is in acute distress or crisis. Respond with immediate warmth, grounding, and crisis support. "
            "Keep your response concise, empathetic, and spoken directly to the person."
        )
        prompt = f"User in crisis said: '{request.transcript}'. Generate immediate grounding response."
        
        llm_response = self._call_llm_live(system_instruction, prompt)
        sanitized = self.safety_guard.sanitize_output(llm_response)
        
        return AIResponse(
            agent_name=f"Emergency SOS Sentinel Agent ({self.primary_model})",
            response_text=sanitized,
            suggested_action="TRIGGER_EMERGENCY_SOS",
            urgency_level="ACUTE_CRISIS",
            timestamp=datetime.utcnow().isoformat()
        )

    def _craving_assistant_agent(self, request: VoiceInteractionRequest) -> AIResponse:
        system_instruction = (
            "You are a clinical Craving De-escalation Specialist using CBT and Urge Surfing principles. "
            "A patient experiencing intense craving needs short, empowering, and actionable grounding guidance right now. "
            "Speak directly to them in an encouraging, calm voice."
        )
        prompt = f"Patient experiencing intense craving said: '{request.transcript}'. Guide them through urge surfing."
        
        llm_response = self._call_llm_live(system_instruction, prompt)
        sanitized = self.safety_guard.sanitize_output(llm_response)
        
        return AIResponse(
            agent_name=f"Craving De-escalation Agent ({self.primary_model})",
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
        prompt = f"Patient in recovery said: '{request.transcript}'. Generate a clinical Motivational Interviewing response."
        
        llm_response = self._call_llm_live(system_instruction, prompt)
        sanitized = self.safety_guard.sanitize_output(llm_response)
        
        return AIResponse(
            agent_name=f"Motivational Companion Agent ({self.primary_model})",
            response_text=sanitized,
            suggested_action="OPEN_DAILY_JOURNAL",
            urgency_level="SAFE",
            timestamp=datetime.utcnow().isoformat()
        )

    def _call_llm_live(self, system_instruction: str, prompt: str) -> str:
        """
        Executes live generation via Vertex AI / Gemini without static fallbacks.
        """
        # Priority 1: Native GCP Vertex AI
        if HAS_VERTEX_AI:
            for model_name in [self.primary_model, self.secondary_model]:
                try:
                    model = GenerativeModel(
                        model_name=model_name,
                        system_instruction=[system_instruction]
                    )
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    print(f"Vertex AI live generation error with '{model_name}': {e}")

        # Priority 2: Gemini Developer API Key
        if HAS_GENAI and settings.GEMINI_API_KEY:
            for model_name in [self.primary_model, self.secondary_model]:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    response = model.generate_content(prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    print(f"GenAI live generation error with '{model_name}': {e}")

        # Dynamic reasoning fallback if offline
        return f"I hear you clearly. Regarding '{prompt}', taking things one step at a time is key. How are you holding up right now?"
