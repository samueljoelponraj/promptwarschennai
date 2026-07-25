import os
from pydantic import BaseModel

class AppSettings(BaseModel):
    APP_NAME: str = "ResilienceAI Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "production"
    
    # AI Settings
    DEFAULT_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CRISIS_THRESHOLD: float = 0.75
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]

settings = AppSettings()
