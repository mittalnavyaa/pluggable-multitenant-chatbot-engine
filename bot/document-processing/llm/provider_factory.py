"""Factory for creating configured LLM providers."""

from __future__ import annotations

from config.settings import Settings
from llm.base_provider import BaseLLMProvider, LLMProviderError
from llm.groq_provider import GroqProvider


class ProviderFactory:
    """Create an LLM provider from runtime settings."""

    @staticmethod
    def create(settings: Settings | None = None) -> BaseLLMProvider:
        config = settings or Settings.from_env()
        if config.provider == "groq":
            return GroqProvider(config)
        raise LLMProviderError(f"Unsupported LLM provider: {config.provider}")
