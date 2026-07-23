"""POST /extract — transcript (or stored transcript_id) -> ExtractedCall."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_session
from app.db.models import Extraction, Transcript
from app.schemas.api import ExtractRequest, ExtractResponse
from app.services.extraction import extract_call

router = APIRouter(tags=["extract"])


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    req: ExtractRequest,
    session: AsyncSession = Depends(get_session),
) -> ExtractResponse:
    settings = get_settings()

    # Resolve the transcript: either look up a stored one, or persist the new text.
    if req.transcript_id is not None:
        transcript = await session.get(Transcript, req.transcript_id)
        if transcript is None:
            raise HTTPException(status_code=404, detail="transcript_id not found")
    else:
        if len(req.transcript) > settings.max_transcript_chars:
            raise HTTPException(
                status_code=413,
                detail=f"Transcript exceeds {settings.max_transcript_chars} characters",
            )
        transcript = Transcript(source_type="text", content=req.transcript)
        session.add(transcript)
        await session.flush()  # assigns transcript.id

    # LLM/provider failures propagate as LLMError and are mapped by the global handler.
    extracted = await extract_call(transcript.content)

    extraction = Extraction(
        transcript_id=transcript.id,
        data=extracted.model_dump(mode="json"),
        model=settings.openai_extraction_model,
    )
    session.add(extraction)
    await session.commit()
    await session.refresh(extraction)

    return ExtractResponse(
        extraction_id=extraction.id,
        transcript_id=transcript.id,
        extracted_call=extracted,
    )
