"""Request/response envelopes for the FastAPI endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.extraction import ExtractedCall
from app.schemas.generation import GenerateResponse


class ExtractRequest(BaseModel):
    transcript: str | None = Field(
        default=None, description="Raw transcript text to extract from."
    )
    transcript_id: int | None = Field(
        default=None, description="ID of a previously stored transcript."
    )

    @model_validator(mode="after")
    def _one_of(self) -> "ExtractRequest":
        if not self.transcript and self.transcript_id is None:
            raise ValueError("Provide either 'transcript' or 'transcript_id'.")
        return self


class ExtractResponse(BaseModel):
    extraction_id: int
    transcript_id: int
    extracted_call: ExtractedCall


class GenerateRequest(BaseModel):
    extraction_id: int | None = Field(
        default=None, description="ID of a stored extraction to generate from."
    )
    extracted_call: ExtractedCall | None = Field(
        default=None, description="An inline extracted structure to generate from."
    )

    @model_validator(mode="after")
    def _one_of(self) -> "GenerateRequest":
        if self.extraction_id is None and self.extracted_call is None:
            raise ValueError("Provide either 'extraction_id' or 'extracted_call'.")
        return self


class GenerateResponseEnvelope(BaseModel):
    generated_output_id: int | None = Field(
        default=None,
        description="Row id if persisted (null when generating from inline input).",
    )
    result: GenerateResponse


class TranscribeResponse(BaseModel):
    transcript_id: int
    transcript: str


class CallRecord(BaseModel):
    transcript_id: int
    source_type: str
    transcript: str
    extraction: ExtractedCall | None = None
    generated_output: GenerateResponse | None = None
