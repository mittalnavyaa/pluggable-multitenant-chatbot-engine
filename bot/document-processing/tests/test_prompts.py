"""Tests for prompt template quality constraints."""

from __future__ import annotations

from pathlib import Path


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def test_system_prompt_enforces_no_hallucination() -> None:
    prompt = (PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8").lower()

    assert "do not hallucinate" in prompt
    assert "output markdown only" in prompt
    assert "do not summarize" in prompt


def test_cleaning_prompt_preserves_information() -> None:
    prompt = (PROMPTS_DIR / "cleaning_prompt.md").read_text(encoding="utf-8").lower()

    assert "preserve all meaningful content" in prompt
    assert "do not invent" in prompt
    assert "return only the cleaned markdown" in prompt
