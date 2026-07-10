"""Runtime settings for the LLM sanitization pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass

from config.env import load_env


@dataclass(frozen=True)
class Settings:
    """Configuration consumed by LLM providers."""

    provider: str
    groq_api_key: str
    model: str
    timeout: float
    temperature: float
    max_chunk_chars: int

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "Settings":
        load_env(env_file)
        return cls(
            provider=os.getenv("LLM_PROVIDER", "groq").strip().lower(),
            groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile").strip(),
            timeout=float(os.getenv("TIMEOUT", "60")),
            temperature=float(os.getenv("TEMPERATURE", "0")),
            max_chunk_chars=int(os.getenv("MAX_CHUNK_CHARS", "12000")),
        )

