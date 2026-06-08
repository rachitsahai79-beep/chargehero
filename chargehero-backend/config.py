"""Configuration management for ChargeHero backend using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
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
    cors_origins: List[str] = []

    # Database Configuration
    database_url: str

    # Email Configuration (optional)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Logging
    log_level: str = "INFO"

    @field_validator('cors_origins', mode='before')
    @classmethod
    def set_cors_origins(cls, v, info):
        """Set CORS origins based on environment."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]

        if v:  # If explicitly set
            return v

        # Default based on environment
        environment = info.data.get('environment', 'development')
        if environment == 'development':
            return ['http://localhost:3000', 'http://localhost:8000', 'http://localhost:19006']
        else:
            # Production - must be explicitly configured via env var
            return []

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
