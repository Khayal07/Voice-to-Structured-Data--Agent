"""Extraction schema — the single structured representation of a call.

`ExtractedCall` is produced once from the transcript and is the sole input to all
three generators (CRM / tasks / email). It is enforced by OpenAI's structured
output (JSON schema) and re-validated here with Pydantic.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


class Participant(BaseModel):
    name: str = Field(description="Participant's name as mentioned in the transcript.")
    role: str | None = Field(
        default=None,
        description="Role if stated, e.g. 'buyer', 'AE', 'support engineer'.",
    )
    organization: str | None = Field(
        default=None, description="Company/organization if mentioned."
    )
    is_primary_contact: bool = Field(
        default=False,
        description="True for the external party the follow-up email is addressed to.",
    )


class ActionItem(BaseModel):
    description: str = Field(description="The task/next step agreed in the call.")
    owner: str | None = Field(
        default=None,
        description="Participant responsible, or null if not stated. Do not guess.",
    )
    due_date_raw: str | None = Field(
        default=None,
        description="Verbatim deadline mention, e.g. 'next Friday', 'end of Q3'.",
    )
    due_date_iso: str | None = Field(
        default=None,
        description="Normalized YYYY-MM-DD only if confidently inferable, else null.",
    )
    source_quote: str = Field(
        description="A short verbatim span from the transcript supporting this item."
    )


class Decision(BaseModel):
    description: str = Field(description="A decision reached during the call.")
    source_quote: str = Field(
        description="A short verbatim span from the transcript supporting this decision."
    )


class ExtractedCall(BaseModel):
    """Structured representation of a single call/meeting."""

    participants: list[Participant] = Field(default_factory=list)
    summary: str = Field(description="Neutral 2-4 sentence summary of the call.")
    key_points: list[str] = Field(
        default_factory=list, description="Main discussion points."
    )
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    sentiment: Sentiment = Field(description="Overall sentiment/tone of the call.")
    outcome: str = Field(description="Short outcome / next-step-at-a-glance.")
    primary_contact_name: str | None = Field(
        default=None,
        description="Name of the external party to address the follow-up email to.",
    )
