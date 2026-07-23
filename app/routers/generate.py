"""POST /generate — extracted structure -> CRM entry + task list + follow-up email."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Extraction, GeneratedOutput
from app.schemas.api import GenerateRequest, GenerateResponseEnvelope
from app.schemas.extraction import ExtractedCall
from app.services.generation.pipeline import generate_all
from app.services.openai_client import StructuredOutputError

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponseEnvelope)
async def generate(
    req: GenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerateResponseEnvelope:
    # Source the structure either from a stored extraction or inline input.
    extraction: Extraction | None = None
    if req.extraction_id is not None:
        extraction = await session.get(Extraction, req.extraction_id)
        if extraction is None:
            raise HTTPException(status_code=404, detail="extraction_id not found")
        call = ExtractedCall.model_validate(extraction.data)
    else:
        call = req.extracted_call

    try:
        result = await generate_all(call)
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    generated_output_id: int | None = None
    if extraction is not None:
        output = GeneratedOutput(
            extraction_id=extraction.id,
            crm=result.crm.model_dump(mode="json"),
            tasks={"tasks": [t.model_dump(mode="json") for t in result.tasks]},
            email=result.email.model_dump(mode="json"),
        )
        session.add(output)
        await session.commit()
        await session.refresh(output)
        generated_output_id = output.id

    return GenerateResponseEnvelope(
        generated_output_id=generated_output_id, result=result
    )
