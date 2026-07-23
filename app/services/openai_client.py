"""Thin async wrapper around the OpenAI SDK.

Two capabilities are exposed:
- `structured_completion`: a chat completion constrained to a Pydantic schema via
  OpenAI's structured outputs (JSON schema), returning a validated model instance.
- `transcribe_audio`: Whisper transcription of an uploaded audio file.

Keeping this seam small makes the rest of the app trivial to unit test by mocking
these two functions.
"""

from __future__ import annotations

from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(RuntimeError):
    """Raised when the model refuses or returns unparsable structured output."""


_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """Lazily construct a shared AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


async def structured_completion(
    *,
    model: str,
    system: str,
    user: str,
    response_model: type[T],
    temperature: float = 0.0,
) -> T:
    """Run a chat completion whose output is validated against `response_model`."""
    client = get_client()
    completion = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=response_model,
        temperature=temperature,
    )
    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise StructuredOutputError(f"Model refused to answer: {message.refusal}")
    if message.parsed is None:
        raise StructuredOutputError("Model returned no parsable structured output.")
    return message.parsed


async def transcribe_audio(*, model: str, filename: str, data: bytes) -> str:
    """Transcribe audio bytes to text via Whisper."""
    client = get_client()
    result = await client.audio.transcriptions.create(
        model=model,
        file=(filename, data),
    )
    return result.text
