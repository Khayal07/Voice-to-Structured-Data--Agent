"""Integration test: transcript -> extract -> generate (CRM + tasks + email).

The LLM boundary is mocked so the test runs offline and deterministically. It
verifies the layers wire together and that the outputs are internally consistent
with the extracted structure.
"""

import pytest

from app.schemas.extraction import ExtractedCall
from app.schemas.generation import (
    CRMContact,
    CRMEntry,
    DealStage,
    FollowUpEmail,
    Priority,
    Task,
    TaskList,
)
from app.services import extraction as extraction_service
from app.services.generation import crm as crm_gen
from app.services.generation import email as email_gen
from app.services.generation import tasks as tasks_gen
from app.services.generation.pipeline import generate_all

TRANSCRIPT = (
    "Alice (AcmeCorp): Thanks for the demo. We'd like to move forward with a pilot.\n"
    "Bob (Vendor): Great. I'll send over the proposal by next Friday.\n"
    "Alice: Perfect, we'll review it with our team."
)

EXTRACTED = ExtractedCall.model_validate(
    {
        "participants": [
            {
                "name": "Alice",
                "role": "buyer",
                "organization": "AcmeCorp",
                "is_primary_contact": True,
            },
            {"name": "Bob", "role": "vendor", "is_primary_contact": False},
        ],
        "summary": "Acme wants to start a pilot; vendor will send a proposal.",
        "key_points": ["Positive demo", "Pilot interest"],
        "decisions": [
            {
                "description": "Move forward with a pilot",
                "source_quote": "move forward with a pilot",
            }
        ],
        "action_items": [
            {
                "description": "Send the proposal",
                "owner": "Bob",
                "due_date_raw": "next Friday",
                "due_date_iso": None,
                "source_quote": "I'll send over the proposal by next Friday",
            }
        ],
        "sentiment": "positive",
        "outcome": "Pilot agreed; proposal to follow",
        "primary_contact_name": "Alice",
    }
)


@pytest.fixture
def mock_llm(monkeypatch):
    """Patch the structured-output boundary in every layer with a canned dispatcher."""

    async def dispatch(**kwargs):
        model = kwargs["response_model"]
        if model is ExtractedCall:
            return EXTRACTED
        if model is CRMEntry:
            return CRMEntry(
                contact=CRMContact(name="Alice", organization="AcmeCorp", role="buyer"),
                deal_stage=DealStage.qualification,
                sentiment="positive",
                notes="Acme wants a pilot; proposal to follow.",
                next_step="Send the proposal",
                open_action_count=len(EXTRACTED.action_items),
            )
        if model is TaskList:
            return TaskList(
                tasks=[
                    Task(
                        owner=ai.owner or "unassigned",
                        description=ai.description,
                        due_date=ai.due_date_iso,
                        priority=Priority.medium,
                    )
                    for ai in EXTRACTED.action_items
                ]
            )
        if model is FollowUpEmail:
            return FollowUpEmail(
                to=EXTRACTED.primary_contact_name,
                subject="Following up on our call",
                body="Thanks for the call. Next step: send the proposal.\n[Your name]",
            )
        raise AssertionError(f"unexpected response_model {model}")

    for module in (extraction_service, crm_gen, tasks_gen, email_gen):
        monkeypatch.setattr(module, "structured_completion", dispatch)


async def test_full_pipeline_produces_consistent_outputs(mock_llm):
    extracted = await extraction_service.extract_call(TRANSCRIPT)
    result = await generate_all(extracted)

    # All three deliverables are produced.
    assert result.crm is not None
    assert result.email is not None
    assert len(result.tasks) == len(extracted.action_items) == 1

    # Tasks are consistent with the extracted action items.
    assert result.tasks[0].owner == "Bob"
    assert result.crm.open_action_count == 1

    # Email is addressed to the external primary contact.
    assert result.email.to == extracted.primary_contact_name == "Alice"
