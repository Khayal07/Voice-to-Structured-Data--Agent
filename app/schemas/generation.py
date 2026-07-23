"""Generation schemas — the three deliverables produced from `ExtractedCall`.

Each generator consumes the extracted structure (never the raw transcript) and
emits one of these models via a focused structured-output LLM call.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# --- CRM entry ---------------------------------------------------------------
class DealStage(str, Enum):
    prospecting = "prospecting"
    qualification = "qualification"
    proposal = "proposal"
    negotiation = "negotiation"
    closed_won = "closed_won"
    closed_lost = "closed_lost"
    follow_up = "follow_up"


class CRMContact(BaseModel):
    name: str
    organization: str | None = None
    role: str | None = None
    email: str | None = None


class CRMEntry(BaseModel):
    contact: CRMContact
    deal_stage: DealStage = Field(description="Best-fit pipeline stage for this call.")
    sentiment: str = Field(description="Sentiment carried over from the extraction.")
    notes: str = Field(description="Concise CRM notes: summary + key points + decisions.")
    next_step: str = Field(description="The single most important next step.")
    open_action_count: int = Field(description="Number of open action items.")


# --- Task list ---------------------------------------------------------------
class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(BaseModel):
    owner: str = Field(description="Responsible person, or 'unassigned'.")
    description: str
    due_date: str | None = Field(
        default=None, description="ISO date (YYYY-MM-DD) if known, else null."
    )
    priority: Priority = Field(description="Inferred priority.")


class TaskList(BaseModel):
    """Object wrapper so the structured-output root is an object, not an array."""

    tasks: list[Task] = Field(default_factory=list)


# --- Follow-up email ---------------------------------------------------------
class FollowUpEmail(BaseModel):
    to: str = Field(description="Recipient — the external primary contact.")
    subject: str
    body: str = Field(description="Polite, professional email summarizing next steps.")


# --- Combined /generate response ---------------------------------------------
class GenerateResponse(BaseModel):
    crm: CRMEntry
    tasks: list[Task]
    email: FollowUpEmail
