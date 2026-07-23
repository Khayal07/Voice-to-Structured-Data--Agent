"""FastAPI application entrypoint for the Voice-to-Structured-Data Agent."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.config import get_settings
from app.db.database import engine, init_db
from app.routers import calls as calls_router
from app.routers import extract as extract_router
from app.routers import generate as generate_router
from app.routers import transcribe as transcribe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup, dispose the engine on shutdown."""
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title="Voice-to-Structured-Data Agent",
    description=(
        "Turns call/meeting transcripts into structured, actionable output: "
        "a CRM entry, a task list, and a follow-up email draft."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(transcribe_router.router)
app.include_router(extract_router.router)
app.include_router(generate_router.router)
app.include_router(calls_router.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness/readiness probe. Confirms the app is up, config loaded, DB reachable."""
    settings = get_settings()
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "extraction_model": settings.openai_extraction_model,
        "database_connected": db_ok,
    }
