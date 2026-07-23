"""LLM-as-judge for semantic matching of predicted items to ground truth.

Given one predicted item and a list of ground-truth candidate items, the judge
decides which candidate (if any) the prediction means the same thing as. This
handles paraphrasing that exact string matching would miss.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.openai_client import structured_completion

JUDGE_SYSTEM_PROMPT = """\
You compare a predicted item against a numbered list of ground-truth items from a \
call transcript. Decide whether the predicted item refers to the same underlying \
action item or decision as one of the ground-truth items.

- Match on meaning, not wording. Paraphrases, reordering, and different phrasing \
still count as a match if they describe the same thing.
- Return the number of the single best matching ground-truth item.
- If the predicted item does not correspond to any ground-truth item (i.e. it was \
not actually in the transcript), return -1.
"""


class JudgeVerdict(BaseModel):
    match_index: int = Field(
        description="0-based index of the matching ground-truth item, or -1 if none."
    )
    reason: str = Field(description="Brief justification.")


async def judge_match(predicted: str, candidates: list[str]) -> int:
    """Return the index of the candidate the prediction matches, or -1 for none."""
    if not candidates:
        return -1
    numbered = "\n".join(f"{i}. {c}" for i, c in enumerate(candidates))
    user = (
        f"Predicted item:\n{predicted}\n\n"
        f"Ground-truth items:\n{numbered}\n\n"
        "Which ground-truth item does the predicted item match? "
        "Reply with its index, or -1 if none."
    )
    verdict = await structured_completion(
        model=get_settings().openai_extraction_model,
        system=JUDGE_SYSTEM_PROMPT,
        user=user,
        response_model=JudgeVerdict,
    )
    if 0 <= verdict.match_index < len(candidates):
        return verdict.match_index
    return -1
