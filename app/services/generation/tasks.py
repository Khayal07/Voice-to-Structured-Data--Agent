"""Task-list generator: ExtractedCall -> list[Task]."""

from __future__ import annotations

from app.config import get_settings
from app.prompts.tasks import TASKS_SYSTEM_PROMPT
from app.schemas.extraction import ExtractedCall
from app.schemas.generation import Task, TaskList
from app.services.openai_client import structured_completion


async def generate_tasks(call: ExtractedCall) -> list[Task]:
    result = await structured_completion(
        model=get_settings().openai_generation_model,
        system=TASKS_SYSTEM_PROMPT,
        user=call.model_dump_json(indent=2),
        response_model=TaskList,
    )
    return result.tasks
