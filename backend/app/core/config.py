from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    GEMINI_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = ""
    NEWS_API_KEY: str = ""
    MLFLOW_TRACKING_URL: str = "http://localhost:5000"
    SECRET_KEY: str = "CHANGE_ME"
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
