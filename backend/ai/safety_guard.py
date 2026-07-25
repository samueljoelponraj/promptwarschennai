import re

class SafetyGuard:
    """
    Deterministic Safety & Guardrail Layer for Recovery & Crisis Intervention.
    Prevents prompt injection, toxic outputs, and self-harm misinformation.
    """
    
    CRISIS_KEYWORDS = [
        "suicide", "kill myself", "want to die", "end it all", 
        "relapsed heavily", "overdose", "cant live anymore", "can't do this anymore"
    ]
    
    HIGH_CRAVING_KEYWORDS = [
        "want drugs", "need a drink", "craving so bad", "going to buy", 
        "gonna use", "i want to use", "need smoke"
    ]
    
    UNSAFE_MEDICAL_ADVICE_PATTERNS = [
        r"stop taking your medication",
        r"detox by yourself",
        r"take \d+ pills"
    ]

    def evaluate_input_safety(self, transcript: str) -> dict:
        text_lower = transcript.lower()
        
        # Check for acute self-harm or overdose crisis
        for kw in self.CRISIS_KEYWORDS:
            if kw in text_lower:
                return {
                    "is_safe": False,
                    "level": "ACUTE_CRISIS",
                    "reason": f"Detected crisis trigger: '{kw}'"
                }
                
        # Check for high craving
        for kw in self.HIGH_CRAVING_KEYWORDS:
            if kw in text_lower:
                return {
                    "is_safe": True,
                    "level": "HIGH_CRAVING",
                    "reason": f"Detected craving trigger: '{kw}'"
                }
                
        return {
            "is_safe": True,
            "level": "SAFE",
            "reason": "Input passed safety evaluation"
        }

    def sanitize_output(self, response_text: str) -> str:
        # Prevent any accidental unsafe medical recommendations
        for pattern in self.UNSAFE_MEDICAL_ADVICE_PATTERNS:
            if re.search(pattern, response_text, re.IGNORECASE):
                return ("I want to make sure you stay safe. Please consult your prescribing physician or care team "
                        "before changing any medication or detox schedule.")
        return response_text
