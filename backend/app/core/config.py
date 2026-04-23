# core/config.py
#
# Single source of truth for all environment variables.
# WHY pydantic_settings?
# It validates env vars at startup. If a required var is missing,
# the app crashes immediately with a clear error — not silently later.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Existing settings ---
    DATABASE_URL: str
    REDIS_URL: str
    GEMINI_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = ""
    NEWS_API_KEY: str = ""
    MLFLOW_TRACKING_URL: str = "http://localhost:5000"
    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    ENVIRONMENT: str = "development"

    # --- New settings for RAG + Agents ---
    # Groq gives free LLM inference — used by chat agent in Phase 2
    GROQ_API_KEY: str = ""

    # Where Chroma persists its data.
    # WHY configurable? In Docker we mount a volume here.
    # Locally we use /tmp/chroma for simplicity.
    CHROMA_PATH: str = "/tmp/chroma"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
