import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Meeting to Scope of Work Microservice"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Task 1 Knowledge Brain API URL
    TASK1_API_URL: str = os.getenv("TASK1_API_URL", "http://127.0.0.1:8000/api/v1")
    
    # Pricing configuration
    HOURLY_RATE_USD: float = 85.0
    USD_TO_INR: float = 86.5
    
    # Model
    DEFAULT_MODEL: str = "claude-3-5-sonnet-20241022"
    FAST_MODEL: str = "claude-3-5-haiku-20241022"
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
