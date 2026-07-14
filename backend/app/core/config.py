"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_name: str = "AI-Outreach"
    debug: bool = False
    secret_key: str = "change-me-to-a-random-string"
    allowed_origins: str = "http://localhost:3000"

    # Database — defaults to local SQLite for quick start
    database_url: str = "sqlite+aiosqlite:///./outreach.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # OpenAI
    openai_api_key: str = ""

    # Lead APIs
    apollo_api_key: str = ""
    hunter_api_key: str = ""

    # Email
    email_provider: str = "sendgrid"
    sendgrid_api_key: str = ""
    aws_ses_region: str = "us-east-1"
    aws_ses_access_key: str = ""
    aws_ses_secret_key: str = ""
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    resend_api_key: str = ""

    # Tracking
    tracking_domain: str = "http://localhost:8000"
    open_pixel_secret: str = "change-me"

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
