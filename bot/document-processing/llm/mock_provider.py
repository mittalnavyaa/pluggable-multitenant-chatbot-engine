"""Mock implementation of the LLM provider interface for offline testing."""

from __future__ import annotations

from config.settings import Settings
from llm.base_provider import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns raw text wrapped in clean Markdown headers."""

    provider_name = "mock"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def clean_markdown(
        self,
        raw_text: str,
        system_prompt: str,
        cleaning_prompt: str,
    ) -> str:
        # Return raw text directly, ensuring it starts with standard markdown structure
        clean_text = raw_text.strip()
        if not clean_text.startswith("#"):
            clean_text = f"# Cleaned Document\n\n{clean_text}"
        return clean_text
