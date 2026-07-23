"""FastAPI application entrypoint for the Voice-to-Structured-Data Agent."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.db.database import engine
from app.errors import LLMError
from app.routers import calls as calls_router
from app.routers import extract as extract_router
from app.routers import generate as generate_router
from app.routers import transcribe as transcribe_router

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Dispose the engine on shutdown.

    The database schema is managed by Alembic migrations (applied by the container
    entrypoint via `alembic upgrade head`), so the app does not create tables here.
    """
    logger.info("Starting up")
    yield
    await engine.dispose()
    logger.info("Shut down cleanly")


app = FastAPI(
    title="Voice-to-Structured-Data Agent",
    description=(
        "Turns call/meeting transcripts into structured, actionable output: "
        "a CRM entry, a task list, and a follow-up email draft."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
    """Map LLM/provider failures to clean HTTP responses."""
    logger.warning("LLM error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


app.include_router(transcribe_router.router)
app.include_router(extract_router.router)
app.include_router(generate_router.router)
app.include_router(calls_router.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness/readiness probe. Confirms the app is up, config loaded, DB reachable."""
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
        "generation_model": settings.openai_generation_model,
        "database_connected": db_ok,
    }
