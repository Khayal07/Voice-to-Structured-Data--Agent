"""Generation orchestrator: run the three generators over one ExtractedCall.

All three consume the same extracted structure (never the raw transcript) and run
concurrently since they share no state.
"""

from __future__ import annotations

import asyncio

from app.schemas.extraction import ExtractedCall
from app.schemas.generation import GenerateResponse
from app.services.generation.crm import generate_crm
from app.services.generation.email import generate_email
from app.services.generation.tasks import generate_tasks


async def generate_all(call: ExtractedCall) -> GenerateResponse:
    crm, tasks, email = await asyncio.gather(
        generate_crm(call),
        generate_tasks(call),
        generate_email(call),
    )
    return GenerateResponse(crm=crm, tasks=tasks, email=email)
