"""FastAPI application entrypoint for the Voice-to-Structured-Data Agent."""

from fastapi import FastAPI

from app.config import get_settings

app = FastAPI(
    title="Voice-to-Structured-Data Agent",
    description=(
        "Turns call/meeting transcripts into structured, actionable output: "
        "a CRM entry, a task list, and a follow-up email draft."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness/readiness probe. Confirms the app is up and config is loaded."""
    settings = get_settings()
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "extraction_model": settings.openai_extraction_model,
    }
