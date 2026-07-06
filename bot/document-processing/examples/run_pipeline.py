"""Run the complete document processing pipeline from the command line."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from time import perf_counter

from exceptions.extraction_exceptions import UnsupportedFileTypeError
from extractors.extractor_factory import ExtractorFactory
from llm.base_provider import LLMAuthenticationError, LLMProviderError, LLMTimeoutError
from pipeline.markdown_writer import MarkdownWriter
from pipeline.sanitizer import MarkdownSanitizer
from utils.logger import get_logger


SUCCESS_EXIT_CODE = 0
USER_ERROR_EXIT_CODE = 1
LLM_ERROR_EXIT_CODE = 2
UNEXPECTED_ERROR_EXIT_CODE = 3


class PipelineRunner:
    """Orchestrates extraction, sanitization, and Markdown output reporting."""

    def __init__(self, output_dir: str | Path = "output") -> None:
        self.writer = MarkdownWriter(output_dir)
        self.logger = get_logger(self.__class__.__name__)

    def run(self, file_path: str | Path) -> int:
        started_at = perf_counter()
        path = Path(file_path)

        self._print_header(path)

        try:
            extractor = ExtractorFactory.create(path)
            extraction_result = extractor.extract(path)
            if not extraction_result.success:
                return self._fail(
                    "Text extraction failed.",
                    extraction_result.errors,
                    USER_ERROR_EXIT_CODE,
                )

            print("Step 1")
            print("[OK] File validated")
            print()

            print("Step 2")
            print(f"[OK] {path.suffix.upper().lstrip('.')} detected")
            print()

            print("Step 3")
            print("[OK] Text extracted")
            print()
            self._print_extraction_stats(extraction_result)

            sanitizer = MarkdownSanitizer(writer=self.writer)
            markdown_result = sanitizer.sanitize(extraction_result)
            if not markdown_result.success:
                return self._handle_sanitization_failure(markdown_result.errors)

            print("Step 4")
            print("[OK] LLM sanitization completed")
            print()
            print("Provider:")
            print(markdown_result.provider.title())
            print()
            print("Model:")
            print(markdown_result.model)
            print()

            output_path = self._output_path(extraction_result.file_name)
            print("Step 5")
            print("[OK] Markdown saved")
            print()
            print("Output:")
            print(output_path.as_posix())
            print()
            print("Total Time:")
            print(f"{perf_counter() - started_at:.2f} seconds")
            print()
            self._print_success_footer()
            return SUCCESS_EXIT_CODE

        except UnsupportedFileTypeError as exc:
            return self._fail("Unsupported file type.", [str(exc)], USER_ERROR_EXIT_CODE)
        except LLMAuthenticationError as exc:
            return self._fail("Invalid LLM API key.", [str(exc)], LLM_ERROR_EXIT_CODE)
        except LLMTimeoutError as exc:
            return self._fail("LLM request timed out.", [str(exc)], LLM_ERROR_EXIT_CODE)
        except LLMProviderError as exc:
            return self._fail("LLM provider failed.", [str(exc)], LLM_ERROR_EXIT_CODE)
        except KeyboardInterrupt:
            return self._fail("Pipeline interrupted by user.", [], USER_ERROR_EXIT_CODE)
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            self.logger.exception("pipeline_failed_unexpected", extra={"error": str(exc)})
            return self._fail(
                "Unexpected pipeline error.",
                [str(exc)],
                UNEXPECTED_ERROR_EXIT_CODE,
            )

    @staticmethod
    def _print_header(path: Path) -> None:
        print("==========================================")
        print("Document Processing Pipeline")
        print("==========================================")
        print()
        print("Input File:")
        print(path.name)
        print()

    @staticmethod
    def _print_success_footer() -> None:
        print("==========================================")
        print("Pipeline Completed Successfully")
        print("==========================================")

    @staticmethod
    def _print_error_footer() -> None:
        print("==========================================")
        print("Pipeline Failed")
        print("==========================================")

    @staticmethod
    def _print_extraction_stats(extraction_result) -> None:
        print(f"File name: {extraction_result.file_name}")
        print(f"File type: {extraction_result.file_extension}")
        print(f"Pages: {extraction_result.page_count}")
        print(f"Words: {extraction_result.word_count}")
        print(f"Characters: {extraction_result.character_count}")
        print(f"Processing time: {extraction_result.processing_time:.2f} seconds")
        print()

    def _output_path(self, source_file_name: str) -> Path:
        return self.writer.output_dir / self.writer._to_markdown_name(source_file_name)

    def _handle_sanitization_failure(self, errors: list[str]) -> int:
        message = "LLM sanitization failed."
        joined = " ".join(errors).lower()
        if "api key" in joined or "unauthorized" in joined:
            message = "Invalid LLM API key."
        elif "timed out" in joined or "timeout" in joined:
            message = "LLM request timed out."
        elif "no raw text" in joined:
            message = "Input document did not contain extractable text."
            return self._fail(message, errors, USER_ERROR_EXIT_CODE)
        return self._fail(message, errors, LLM_ERROR_EXIT_CODE)

    def _fail(self, title: str, errors: list[str], exit_code: int) -> int:
        self.logger.error("pipeline_failed", extra={"error": title})
        print("Error:")
        print(title)
        for error in errors:
            print(f"- {error}")
        print()
        self._print_error_footer()
        return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m examples.run_pipeline",
        description="Run extraction and LLM Markdown sanitization for one document.",
    )
    parser.add_argument(
        "file_path",
        help="Path to a supported .pdf, .docx, or .txt document.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where cleaned Markdown should be saved. Defaults to output/.",
    )
    parser.add_argument(
        "--quiet-logs",
        action="store_true",
        help="Suppress internal logging and show only pipeline output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.quiet_logs:
        logging.disable(logging.CRITICAL)

    runner = PipelineRunner(output_dir=args.output_dir)
    return runner.run(args.file_path)


if __name__ == "__main__":
    sys.exit(main())
