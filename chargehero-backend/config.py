"""Configuration management for ChargeHero backend using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = "development"

    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Twilio Configuration (SMS)
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "ChargeHero Backend"
    api_version: str = "1.0.0"

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database Configuration
    database_url: str

    # Email Configuration (optional)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
