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

    # OpenAI request reliability
    openai_timeout_seconds: float = 60.0
    openai_max_retries: int = 2

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/voice_agent"

    # Ops
    log_level: str = "INFO"
    # Comma-separated list of allowed CORS origins ("*" allows all).
    cors_allow_origins: str = "*"
    # Max accepted transcript length (characters) for /extract.
    max_transcript_chars: int = 100_000
    # Max accepted audio upload size (bytes) for /transcribe. Default 25 MB.
    max_audio_bytes: int = 25 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
