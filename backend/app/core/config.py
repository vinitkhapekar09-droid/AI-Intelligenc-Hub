# core/config.py
#
# Single source of truth for all environment variables.
# WHY pydantic_settings?
# It validates env vars at startup. If a required var is missing,
# the app crashes immediately with a clear error — not silently later.

import json

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Existing settings ---
    DATABASE_URL: str
    REDIS_URL: str
    GEMINI_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = ""
    NEWS_API_KEY: str = ""
    MLFLOW_TRACKING_URL: str = ""
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    AUTO_CREATE_SCHEMA: bool = True
    TRIGGER_DIGEST_TOKEN: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 768

    # --- New settings for RAG + Agents ---
    # Groq gives free LLM inference — used by chat agent in Phase 2
    GROQ_API_KEY: str = ""

    APP_BASE_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", enable_decoding=False)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw_value = value.strip()
            if raw_value.startswith("["):
                return json.loads(raw_value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT.lower() != "production":
            return self

        if self.SECRET_KEY == "CHANGE_ME":
            raise ValueError("SECRET_KEY must be set to a secure value in production")

        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must include at least one frontend origin in production")

        if not self.TRIGGER_DIGEST_TOKEN:
            raise ValueError("TRIGGER_DIGEST_TOKEN must be set in production")

        return self


settings = Settings()
