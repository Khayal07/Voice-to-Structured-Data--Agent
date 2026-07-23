"""POST /transcribe — audio upload -> transcript text (stored)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_session
from app.db.models import Transcript
from app.schemas.api import TranscribeResponse
from app.services.transcription import transcribe

router = APIRouter(tags=["transcribe"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_endpoint(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> TranscribeResponse:
    settings = get_settings()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio file")
    if len(data) > settings.max_audio_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Audio exceeds {settings.max_audio_bytes} bytes",
        )

    text = await transcribe(file.filename or "audio", data)

    transcript = Transcript(source_type="audio", content=text)
    session.add(transcript)
    await session.commit()
    await session.refresh(transcript)

    return TranscribeResponse(transcript_id=transcript.id, transcript=text)
