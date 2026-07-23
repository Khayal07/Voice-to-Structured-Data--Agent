"""CRM-entry generator: ExtractedCall -> CRMEntry."""

from __future__ import annotations

from app.config import get_settings
from app.prompts.crm import CRM_SYSTEM_PROMPT
from app.schemas.extraction import ExtractedCall
from app.schemas.generation import CRMEntry
from app.services.openai_client import structured_completion


async def generate_crm(call: ExtractedCall) -> CRMEntry:
    return await structured_completion(
        model=get_settings().openai_extraction_model,
        system=CRM_SYSTEM_PROMPT,
        user=call.model_dump_json(indent=2),
        response_model=CRMEntry,
    )
