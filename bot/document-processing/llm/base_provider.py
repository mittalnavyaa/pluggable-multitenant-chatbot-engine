"""Base abstraction for Markdown-cleaning LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""


class LLMAuthenticationError(LLMProviderError):
    """Raised when the configured provider credentials are invalid."""


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM request times out."""


class BaseLLMProvider(ABC):
    """Provider interface used by the sanitization pipeline."""

    provider_name: str
    model: str

    @abstractmethod
    def clean_markdown(
        self,
        raw_text: str,
        system_prompt: str,
        cleaning_prompt: str,
    ) -> str:
        """Return cleaned Markdown for raw extracted text."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        """Query LLM model using standard chat messages list."""
