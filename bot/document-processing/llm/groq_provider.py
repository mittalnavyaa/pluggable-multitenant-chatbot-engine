"""Groq implementation of the LLM provider interface."""

from __future__ import annotations

import logging
import time
import requests

from config.settings import Settings
from llm.base_provider import (
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMProviderError,
    LLMTimeoutError,
)

logger = logging.getLogger("GroqProvider")


class GroqProvider(BaseLLMProvider):
    """LLM provider that calls Groq's OpenAI-compatible chat API."""

    provider_name = "groq"
    api_url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.model
        if not settings.groq_api_key:
            raise LLMAuthenticationError("GROQ_API_KEY is not configured.")
    def _execute_request(self, payload: dict) -> str:
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        max_retries = 3
        backoff_factor = 2.0
        initial_delay = 2.0

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.settings.timeout,
                )
            except requests.Timeout as exc:
                if attempt == max_retries:
                    raise LLMTimeoutError("Groq request timed out.") from exc
                delay = initial_delay * (backoff_factor ** attempt)
                logger.warning(f"Groq request timed out. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            except requests.RequestException as exc:
                if attempt == max_retries:
                    raise LLMProviderError(f"Groq request failed: {exc}") from exc
                delay = initial_delay * (backoff_factor ** attempt)
                logger.warning(f"Groq request failed: {exc}. Retrying in {delay}s...")
                time.sleep(delay)
                continue

            if response.status_code in {401, 403}:
                raise LLMAuthenticationError("Groq API key is invalid or unauthorized.")

            is_rate_limit = (
                response.status_code == 429 or
                (response.status_code == 413 and "rate_limit_exceeded" in response.text)
            )

            if is_rate_limit and attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        pass
                logger.warning(
                    f"Rate limit hit (status {response.status_code}). "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                continue

            if response.status_code >= 400:
                raise LLMProviderError(
                    f"Groq request failed with status {response.status_code}: "
                    f"{response.text}"
                )

            break

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMProviderError("Groq response did not contain expected content.") from exc

        return content.strip()

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
        return self._execute_request(payload)

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": messages,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return self._execute_request(payload)
