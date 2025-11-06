"""
Application configuration using Pydantic Settings.
All settings are loaded from environment variables with type validation.
"""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "ASX Announcements SaaS"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = Field(
        ..., description="PostgreSQL connection URL"
    )
    database_pool_size: int = Field(default=10, ge=1, le=50)
    database_max_overflow: int = Field(default=20, ge=0, le=100)

    # Storage
    storage_type: Literal["local", "s3", "r2"] = "local"
    local_storage_path: str = "./data/pdfs"
    s3_bucket_name: str = ""
    s3_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    cloudflare_r2_endpoint: str = ""
    cloudflare_r2_access_key_id: str = ""
    cloudflare_r2_secret_access_key: str = ""

    # LLM Configuration (Google Gemini)
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = "gemini-1.5-pro"
    gemini_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(default=2048, ge=256, le=8192)

    # Scraper
    asx_url: str = "https://www.asx.com.au/asx/v2/statistics/todayAnns.do"
    scrape_interval_minutes: int = Field(default=60, ge=5, le=1440)
    max_concurrent_downloads: int = Field(default=5, ge=1, le=20)
    request_timeout_seconds: int = Field(default=30, ge=5, le=120)
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Authentication & Security
    jwt_secret_key: str = Field(..., description="Secret key for JWT token signing")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=60, ge=5, le=10080)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_monthly_price_id: str = ""
    stripe_yearly_price_id: str = ""

    # Subscription
    free_trial_days: int = Field(default=7, ge=0, le=90)
    monthly_plan_price: int = Field(default=20, ge=1)
    yearly_plan_price: int = Field(default=200, ge=1)

    # Stock Data
    yfinance_cache_hours: int = Field(default=1, ge=0, le=24)
    stock_data_retry_attempts: int = Field(default=3, ge=1, le=10)
    stock_data_retry_delay_seconds: int = Field(default=5, ge=1, le=60)

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, ge=1)
    rate_limit_per_hour: int = Field(default=1000, ge=1)

    # Background Jobs
    scheduler_timezone: str = "Australia/Sydney"
    scheduler_max_instances: int = 1

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


# Global settings instance
settings = Settings()
