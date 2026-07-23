"""Extraction service: transcript -> validated ExtractedCall."""

from __future__ import annotations

from app.config import get_settings
from app.prompts.extraction import EXTRACTION_SYSTEM_PROMPT, build_user_prompt
from app.schemas.extraction import ExtractedCall
from app.services.openai_client import structured_completion


async def extract_call(transcript: str) -> ExtractedCall:
    """Run structured extraction over a transcript."""
    settings = get_settings()
    return await structured_completion(
        model=settings.openai_extraction_model,
        system=EXTRACTION_SYSTEM_PROMPT,
        user=build_user_prompt(transcript),
        response_model=ExtractedCall,
    )
