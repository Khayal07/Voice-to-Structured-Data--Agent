"""Domain error types mapped to HTTP responses by the app exception handler.

Keeping these decoupled from FastAPI means services can raise meaningful errors
without importing web-framework types, and the API layer maps them to status codes
in one place (see app.main).
"""

from __future__ import annotations


class LLMError(RuntimeError):
    """Base class for failures talking to the LLM provider."""

    status_code: int = 502
    detail: str = "LLM provider error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.detail)


class StructuredOutputError(LLMError):
    """The model refused or returned unparsable structured output."""

    status_code = 502
    detail = "The model returned invalid or no structured output"


class LLMAuthError(LLMError):
    """Authentication with the provider failed (bad/missing API key)."""

    status_code = 500  # server misconfiguration, not the caller's fault
    detail = "LLM authentication failed — check OPENAI_API_KEY"


class LLMRateLimitError(LLMError):
    """The provider rate-limited the request."""

    status_code = 503
    detail = "LLM provider rate limit reached — try again shortly"


class LLMUnavailableError(LLMError):
    """The provider timed out or was otherwise unreachable."""

    status_code = 503
    detail = "LLM provider is unavailable or timed out"
