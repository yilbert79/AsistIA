from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")
    database_url: str = "sqlite:///./asistia.db"
    app_env: str = "development"
    seed_demo_data: bool = True
    secret_key: str = "dev-only-change-this-before-deployment"
    token_ttl_minutes: int = 240
    dev_admin_email: str = "admin@asistia.example.com"
    dev_admin_password: str = "AsistIA-demo-2026"
    ai_provider: str = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

settings = Settings()
