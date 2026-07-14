"""Mock implementation of the LLM provider interface for offline testing."""

from __future__ import annotations

from config.settings import Settings
from llm.base_provider import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns raw text wrapped in clean Markdown headers."""

    provider_name = "mock"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.model

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

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        # Return mock JSON response if it looks like an intent classification prompt
        content_lower = "".join([m.get("content", "") for m in messages]).lower()
        if "intent" in content_lower or "taxonomy" in content_lower:
            return """{
  "intent": "Pricing",
  "confidence": 0.95,
  "secondary_intents": [
    "General Information"
  ],
  "reasoning": [
    "User asked for details regarding course fees and pricing options.",
    "Assistant explained the payment installments."
  ]
}"""
        return "Mock text response."
