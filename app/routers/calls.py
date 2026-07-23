"""GET /calls/{transcript_id} — fetch a stored call with its extraction and outputs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Extraction, GeneratedOutput, Transcript
from app.schemas.api import CallRecord
from app.schemas.extraction import ExtractedCall
from app.schemas.generation import CRMEntry, FollowUpEmail, GenerateResponse, Task

router = APIRouter(tags=["calls"])


@router.get("/calls/{transcript_id}", response_model=CallRecord)
async def get_call(
    transcript_id: int,
    session: AsyncSession = Depends(get_session),
) -> CallRecord:
    transcript = await session.get(Transcript, transcript_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="transcript not found")

    # Most recent extraction for this transcript, if any.
    extraction = (
        await session.execute(
            select(Extraction)
            .where(Extraction.transcript_id == transcript_id)
            .order_by(Extraction.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    extracted_call = None
    generated = None
    if extraction is not None:
        extracted_call = ExtractedCall.model_validate(extraction.data)

        output = (
            await session.execute(
                select(GeneratedOutput)
                .where(GeneratedOutput.extraction_id == extraction.id)
                .order_by(GeneratedOutput.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if output is not None:
            generated = GenerateResponse(
                crm=CRMEntry.model_validate(output.crm),
                tasks=[Task.model_validate(t) for t in output.tasks.get("tasks", [])],
                email=FollowUpEmail.model_validate(output.email),
            )

    return CallRecord(
        transcript_id=transcript.id,
        source_type=transcript.source_type,
        transcript=transcript.content,
        extraction=extracted_call,
        generated_output=generated,
    )
