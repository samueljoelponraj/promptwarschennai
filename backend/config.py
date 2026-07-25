import os
from pydantic import BaseModel

class AppSettings(BaseModel):
    APP_NAME: str = "ResilienceAI Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "production"
    
    # GCP Vertex AI Settings
    GCP_PROJECT: str = os.getenv("GCP_PROJECT", "salesforce-503116")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash-native-audio")
    SECONDARY_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CRISIS_THRESHOLD: float = 0.75
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]

settings = AppSettings()
