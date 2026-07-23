"""Unit tests for structured-output schema validation and malformed input handling."""

import pytest
from pydantic import ValidationError

from app.schemas.extraction import ExtractedCall, Sentiment

VALID_PAYLOAD = {
    "participants": [
        {
            "name": "Jane Doe",
            "role": "buyer",
            "organization": "Acme",
            "is_primary_contact": True,
        }
    ],
    "summary": "Discussed rollout timeline.",
    "key_points": ["Timeline", "Pricing"],
    "decisions": [
        {"description": "Proceed with pilot", "source_quote": "let's do the pilot"}
    ],
    "action_items": [
        {
            "description": "Send proposal",
            "owner": "Jane Doe",
            "due_date_raw": "next Friday",
            "due_date_iso": None,
            "source_quote": "send the proposal by next Friday",
        }
    ],
    "sentiment": "positive",
    "outcome": "Pilot agreed",
    "primary_contact_name": "Jane Doe",
}


def test_valid_payload_parses():
    call = ExtractedCall.model_validate(VALID_PAYLOAD)
    assert call.sentiment is Sentiment.positive
    assert call.action_items[0].owner == "Jane Doe"
    assert call.participants[0].is_primary_contact is True


def test_optional_fields_default_to_none():
    call = ExtractedCall.model_validate(
        {
            "summary": "s",
            "sentiment": "neutral",
            "outcome": "o",
            "action_items": [{"description": "d", "source_quote": "q"}],
        }
    )
    # Missing optionals default sensibly instead of raising.
    assert call.participants == []
    assert call.primary_contact_name is None
    ai = call.action_items[0]
    assert ai.owner is None and ai.due_date_iso is None


def test_missing_required_field_raises():
    bad = dict(VALID_PAYLOAD)
    del bad["summary"]  # required
    with pytest.raises(ValidationError):
        ExtractedCall.model_validate(bad)


def test_action_item_requires_source_quote():
    with pytest.raises(ValidationError):
        ExtractedCall.model_validate(
            {
                "summary": "s",
                "sentiment": "neutral",
                "outcome": "o",
                "action_items": [{"description": "no quote here"}],
            }
        )


def test_invalid_sentiment_enum_rejected():
    bad = dict(VALID_PAYLOAD)
    bad["sentiment"] = "ecstatic"
    with pytest.raises(ValidationError):
        ExtractedCall.model_validate(bad)


def test_malformed_json_string_rejected():
    with pytest.raises(ValidationError):
        ExtractedCall.model_validate_json('{"summary": "s", "sentiment":')
