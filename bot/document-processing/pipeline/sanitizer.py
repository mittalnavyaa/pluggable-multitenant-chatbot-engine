"""AI Markdown sanitization pipeline."""

from __future__ import annotations

from pathlib import Path
import re
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
            chunks = self._split_text_into_chunks(extraction_result.raw_text)
            cleaned_markdowns = []
            system_prompt = self._load_prompt("system_prompt.md")
            cleaning_prompt = self._load_prompt("cleaning_prompt.md")

            for idx, chunk in enumerate(chunks, 1):
                self.logger.info(
                    f"Sanitizing chunk {idx}/{len(chunks)} ({len(chunk)} characters)..."
                )
                cleaned_chunk = self.provider.clean_markdown(
                    raw_text=chunk,
                    system_prompt=system_prompt,
                    cleaning_prompt=cleaning_prompt,
                )
                cleaned_markdowns.append(cleaned_chunk)

            markdown = "\n\n".join(cleaned_markdowns)
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

    def _split_text_into_chunks(self, raw_text: str) -> list[str]:
        settings = getattr(self.provider, "settings", None)
        max_chars = getattr(settings, "max_chunk_chars", 12000) if settings else 12000

        parts = re.split(r"(<!-- PAGE_NUMBER: \d+ -->)", raw_text)

        pages = []
        if len(parts) > 1:
            preamble = parts[0].strip()
            if preamble:
                pages.append(preamble)
            for i in range(1, len(parts), 2):
                marker = parts[i]
                content = parts[i + 1] if i + 1 < len(parts) else ""
                pages.append(marker + content)
        else:
            pages.append(raw_text)

        chunks = []
        current_chunk = []
        current_len = 0

        for page in pages:
            page_len = len(page)
            if page_len > max_chars:
                # Flush current chunk
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_len = 0

                # Split large page into line-based sub-chunks
                lines = page.splitlines(keepends=True)
                sub_chunk = []
                sub_len = 0
                for line in lines:
                    if len(line) > max_chars:
                        if sub_chunk:
                            chunks.append("".join(sub_chunk))
                            sub_chunk = []
                            sub_len = 0
                        for i in range(0, len(line), max_chars):
                            chunks.append(line[i : i + max_chars])
                    elif sub_len + len(line) > max_chars:
                        if sub_chunk:
                            chunks.append("".join(sub_chunk))
                        sub_chunk = [line]
                        sub_len = len(line)
                    else:
                        sub_chunk.append(line)
                        sub_len += len(line)
                if sub_chunk:
                    chunks.append("".join(sub_chunk))
            else:
                if current_len + page_len > max_chars:
                    chunks.append("".join(current_chunk))
                    current_chunk = [page]
                    current_len = page_len
                else:
                    current_chunk.append(page)
                    current_len += page_len

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks

