"""Groq implementation of the LLM provider interface."""

from __future__ import annotations

import requests

from config.settings import Settings
from llm.base_provider import (
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMProviderError,
    LLMTimeoutError,
)


class GroqProvider(BaseLLMProvider):
    """LLM provider that calls Groq's OpenAI-compatible chat API."""

    provider_name = "groq"
    api_url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.model
        if not settings.groq_api_key:
            raise LLMAuthenticationError("GROQ_API_KEY is not configured.")

    def clean_markdown(
        self,
        raw_text: str,
        system_prompt: str,
        cleaning_prompt: str,
    ) -> str:
        payload = {
            "model": self.model,
            "temperature": self.settings.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"{cleaning_prompt}\n\nRAW TEXT:\n{raw_text}",
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.settings.timeout,
            )
        except requests.Timeout as exc:
            raise LLMTimeoutError("Groq request timed out.") from exc
        except requests.RequestException as exc:
            raise LLMProviderError(f"Groq request failed: {exc}") from exc

        if response.status_code in {401, 403}:
            raise LLMAuthenticationError("Groq API key is invalid or unauthorized.")
        if response.status_code >= 400:
            raise LLMProviderError(
                f"Groq request failed with status {response.status_code}: "
                f"{response.text}"
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMProviderError("Groq response did not contain Markdown content.") from exc

        return content.strip()
