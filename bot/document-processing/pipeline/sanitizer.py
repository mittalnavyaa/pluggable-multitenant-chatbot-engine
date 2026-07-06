"""AI Markdown sanitization pipeline."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from llm.base_provider import BaseLLMProvider, LLMProviderError
from llm.provider_factory import ProviderFactory
from models.clean_markdown_result import CleanMarkdownResult
from models.extraction_result import ExtractionResult
from pipeline.markdown_writer import MarkdownWriter
from utils.logger import get_logger


class MarkdownSanitizer:
    """Convert extracted raw text into clean Markdown using an LLM provider."""

    large_document_threshold = 50_000

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        writer: MarkdownWriter | None = None,
        prompts_dir: str | Path = "prompts",
    ) -> None:
        self.provider = provider or ProviderFactory.create()
        self.writer = writer or MarkdownWriter()
        self.prompts_dir = Path(prompts_dir)
        self.logger = get_logger(self.__class__.__name__)

    def sanitize(self, extraction_result: ExtractionResult) -> CleanMarkdownResult:
        started_at = perf_counter()
        warnings: list[str] = []

        self.logger.info(
            "markdown_sanitization_started",
            extra={"file_path": extraction_result.file_name},
        )

        if not extraction_result.success:
            return self._failed(
                started_at,
                warnings,
                ["Extraction result is not successful."],
            )

        if not extraction_result.raw_text.strip():
            return self._failed(
                started_at,
                warnings,
                ["Extraction result contains no raw text."],
            )

        if extraction_result.character_count > self.large_document_threshold:
            warnings.append(
                "Large document detected; provider context limits may apply."
            )

        try:
            markdown = self.provider.clean_markdown(
                raw_text=extraction_result.raw_text,
                system_prompt=self._load_prompt("system_prompt.md"),
                cleaning_prompt=self._load_prompt("cleaning_prompt.md"),
            )
            self.writer.write(markdown, extraction_result.file_name)
            processing_time = perf_counter() - started_at

            self.logger.info(
                "markdown_sanitization_completed",
                extra={
                    "file_path": extraction_result.file_name,
                    "duration_seconds": round(processing_time, 6),
                },
            )
            return CleanMarkdownResult(
                success=True,
                markdown=markdown,
                processing_time=round(processing_time, 6),
                provider=self.provider.provider_name,
                model=self.provider.model,
                warnings=warnings,
                errors=[],
            )
        except LLMProviderError as exc:
            return self._failed(started_at, warnings, [str(exc)])
        except Exception as exc:  # pragma: no cover - defensive boundary
            self.logger.exception(
                "markdown_sanitization_failed_unexpected",
                extra={"file_path": extraction_result.file_name, "error": str(exc)},
            )
            return self._failed(
                started_at,
                warnings,
                [f"Unexpected sanitization error: {exc}"],
            )

    def _load_prompt(self, file_name: str) -> str:
        return (self.prompts_dir / file_name).read_text(encoding="utf-8").strip()

    def _failed(
        self,
        started_at: float,
        warnings: list[str],
        errors: list[str],
    ) -> CleanMarkdownResult:
        processing_time = perf_counter() - started_at
        for error in errors:
            self.logger.error("markdown_sanitization_failed", extra={"error": error})
        return CleanMarkdownResult(
            success=False,
            markdown="",
            processing_time=round(processing_time, 6),
            provider=self.provider.provider_name,
            model=self.provider.model,
            warnings=warnings,
            errors=errors,
        )
