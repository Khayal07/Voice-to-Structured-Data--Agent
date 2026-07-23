"""Application configuration loaded from environment / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from environment variables (or a local .env)."""

    openai_api_key: str = ""
    # Extraction + judge run on the stronger model (accuracy is critical here).
    openai_extraction_model: str = "gpt-4o"
    # Generators format already-structured data, so a cheaper model is fine.
    openai_generation_model: str = "gpt-4o-mini"
    openai_transcribe_model: str = "whisper-1"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@db:5432/voice_agent"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
