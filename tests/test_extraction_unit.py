"""Unit tests for the extraction service with the OpenAI client mocked."""

import pytest

from app.schemas.extraction import ExtractedCall
from app.services import extraction as extraction_service
from app.services.openai_client import StructuredOutputError

CANNED = ExtractedCall.model_validate(
    {
        "participants": [{"name": "Sam", "is_primary_contact": True}],
        "summary": "A short call.",
        "key_points": ["intro"],
        "decisions": [],
        "action_items": [
            {"description": "Follow up", "owner": "Sam", "source_quote": "I'll follow up"}
        ],
        "sentiment": "neutral",
        "outcome": "Will follow up",
        "primary_contact_name": "Sam",
    }
)


async def test_extract_call_returns_structured_model(monkeypatch):
    async def fake_structured_completion(**kwargs):
        # Service must pass the transcript through and request the right schema.
        assert kwargs["response_model"] is ExtractedCall
        assert "hello world" in kwargs["user"]
        return CANNED

    monkeypatch.setattr(
        extraction_service, "structured_completion", fake_structured_completion
    )
    result = await extraction_service.extract_call("hello world")
    assert result is CANNED
    assert result.action_items[0].owner == "Sam"


async def test_extract_call_propagates_structured_output_error(monkeypatch):
    async def boom(**kwargs):
        raise StructuredOutputError("model refused")

    monkeypatch.setattr(extraction_service, "structured_completion", boom)
    with pytest.raises(StructuredOutputError):
        await extraction_service.extract_call("anything")
