"""Follow-up email generator: ExtractedCall -> FollowUpEmail."""

from __future__ import annotations

from app.config import get_settings
from app.prompts.email import EMAIL_SYSTEM_PROMPT
from app.schemas.extraction import ExtractedCall
from app.schemas.generation import FollowUpEmail
from app.services.openai_client import structured_completion


async def generate_email(call: ExtractedCall) -> FollowUpEmail:
    return await structured_completion(
        model=get_settings().openai_extraction_model,
        system=EMAIL_SYSTEM_PROMPT,
        user=call.model_dump_json(indent=2),
        response_model=FollowUpEmail,
    )
