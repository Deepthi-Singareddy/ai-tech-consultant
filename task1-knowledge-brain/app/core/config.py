import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Knowledge Brain Microservice"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Sitemap & Crawler settings
    SITEMAP_URL: str = "https://support.brilliantdirectories.com/support/sitemap.xml"
    CRAWLER_MAX_WORKERS: int = 3
    CRAWLER_DELAY_SECONDS: float = 0.35
    CRAWLER_TIMEOUT: int = 15
    MAX_RETRIES: int = 3
    
    # Data Paths
    DATA_DIR: Path = BASE_DIR / "data"
    ARTICLES_DIR: Path = DATA_DIR / "articles"
    SCREENSHOTS_DIR: Path = DATA_DIR / "screenshots"
    MANIFEST_FILE: Path = DATA_DIR / "manifest.json"
    INDEX_FILE: Path = DATA_DIR / "index.json"
    ESCALATIONS_FILE: Path = DATA_DIR / "escalations.json"
    
    # RAG Settings
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    CONFIDENCE_THRESHOLD: float = 0.65
    TOP_K: int = 5
    
    # Model & Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEFAULT_MODEL: str = "claude-3-5-sonnet-20241022"
    FAST_MODEL: str = "claude-3-5-haiku-20241022"
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
