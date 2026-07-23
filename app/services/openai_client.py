"""Thin async wrapper around the OpenAI SDK.

Two capabilities are exposed:
- `structured_completion`: a chat completion constrained to a Pydantic schema via
  OpenAI's structured outputs (JSON schema), returning a validated model instance.
- `transcribe_audio`: Whisper transcription of an uploaded audio file.

The wrapper configures timeouts + automatic retries and translates OpenAI SDK
exceptions into the app's domain errors (see app.errors), so callers never handle
provider-specific exception types and the API layer can map them to HTTP codes.
Keeping this seam small also makes the rest of the app trivial to unit test.
"""

from __future__ import annotations

import logging
from typing import TypeVar

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from pydantic import BaseModel

from app.config import get_settings

# Re-exported for backwards-compatible imports elsewhere.
from app.errors import (  # noqa: F401
    LLMAuthError,
    LLMError,
    LLMRateLimitError,
    LLMUnavailableError,
    StructuredOutputError,
)

logger = logging.getLogger("app.openai")

T = TypeVar("T", bound=BaseModel)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """Lazily construct a shared AsyncOpenAI client with timeout + retries."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
    return _client


def _translate(exc: Exception) -> LLMError:
    """Map an OpenAI SDK exception to a domain error."""
    if isinstance(exc, AuthenticationError):
        return LLMAuthError(str(exc))
    if isinstance(exc, RateLimitError):
        return LLMRateLimitError(str(exc))
    if isinstance(exc, APITimeoutError | APIConnectionError):
        return LLMUnavailableError(str(exc))
    if isinstance(exc, APIError):
        return LLMUnavailableError(str(exc))
    return LLMError(str(exc))


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
    try:
        completion = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=response_model,
            temperature=temperature,
        )
    except (APIError, APITimeoutError, APIConnectionError) as exc:
        logger.warning("structured_completion failed: %s", exc)
        raise _translate(exc) from exc

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise StructuredOutputError(f"Model refused to answer: {message.refusal}")
    if message.parsed is None:
        raise StructuredOutputError("Model returned no parsable structured output.")
    return message.parsed


async def transcribe_audio(*, model: str, filename: str, data: bytes) -> str:
    """Transcribe audio bytes to text via Whisper."""
    client = get_client()
    try:
        result = await client.audio.transcriptions.create(
            model=model,
            file=(filename, data),
        )
    except (APIError, APITimeoutError, APIConnectionError) as exc:
        logger.warning("transcribe_audio failed: %s", exc)
        raise _translate(exc) from exc
    return result.text
