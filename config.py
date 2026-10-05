import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration class loaded from environment variables."""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-2026")
    
    # SQLite Database configuration - using absolute path for robustness on Windows
    DATABASE_PATH = (BASE_DIR / "database" / "inventory.db").resolve()
    env_db = os.getenv("DATABASE_URL")
    if env_db and not env_db.startswith("sqlite:///database"):
        SQLALCHEMY_DATABASE_URI = env_db
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Microsoft Foundry / Azure OpenAI Configuration
    AOAI_ENDPOINT = (os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("FOUNDRY_ENDPOINT", "")).strip().rstrip("/")
    AOAI_KEY = (os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("FOUNDRY_API_KEY", "")).strip()
    TEXT_MODEL = (os.getenv("TEXT_MODEL_DEPLOYMENT") or os.getenv("FOUNDRY_DEPLOYMENT_NAME", "gpt-4.1-mini")).strip()
    VISION_MODEL = (os.getenv("VISION_MODEL_DEPLOYMENT") or TEXT_MODEL).strip()
    IMAGE_MODEL = os.getenv("IMAGE_MODEL_DEPLOYMENT", "FLUX.2-flex").strip()

    # Speech Service
    SPEECH_ENDPOINT = os.getenv("SPEECH_ENDPOINT", "").strip().rstrip("/")
    SPEECH_KEY = os.getenv("SPEECH_API_KEY", "").strip()
    SPEECH_REGION = os.getenv("SPEECH_REGION", "eastus").strip()

    # Content Understanding
    CONTENT_ENDPOINT = os.getenv("CONTENT_ENDPOINT", "").strip().rstrip("/")
    CONTENT_KEY = os.getenv("CONTENT_API_KEY", "").strip()
    CONTENT_API_VERSION = os.getenv("CONTENT_API_VERSION", "2025-11-01").strip()

    # Foundry Aliases
    FOUNDRY_ENDPOINT = AOAI_ENDPOINT
    FOUNDRY_API_KEY = AOAI_KEY
    FOUNDRY_DEPLOYMENT_NAME = TEXT_MODEL
    FOUNDRY_API_VERSION = os.getenv("FOUNDRY_API_VERSION", "2024-06-01").strip()
    
    # Server & Uploads
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "1") in ("1", "true", "True")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    UPLOAD_FOLDER = str((BASE_DIR / "uploads").resolve())

    @classmethod
    def is_foundry_configured(cls) -> bool:
        """Validate whether valid Microsoft Foundry / Azure OpenAI credentials have been supplied."""
        placeholders = {
            "YOUR_MICROSOFT_FOUNDRY_ENDPOINT",
            "YOUR_MICROSOFT_FOUNDRY_API_KEY",
            "YOUR_DEPLOYMENT_NAME",
            "YOUR_API_VERSION",
            ""
        }
        has_endpoint = cls.AOAI_ENDPOINT not in placeholders and bool(cls.AOAI_ENDPOINT)
        has_key = cls.AOAI_KEY not in placeholders and bool(cls.AOAI_KEY)
        has_deployment = cls.TEXT_MODEL not in placeholders and bool(cls.TEXT_MODEL)
        return has_endpoint and has_key and has_deployment
