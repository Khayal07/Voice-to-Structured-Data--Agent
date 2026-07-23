"""Transcription service: audio bytes -> text via Whisper."""

from __future__ import annotations

from app.config import get_settings
from app.services.openai_client import transcribe_audio


async def transcribe(filename: str, data: bytes) -> str:
    return await transcribe_audio(
        model=get_settings().openai_transcribe_model,
        filename=filename,
        data=data,
    )
