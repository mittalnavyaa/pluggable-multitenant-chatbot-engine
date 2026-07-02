"""Markdown output writer."""

from __future__ import annotations

import re
from pathlib import Path


class MarkdownWriter:
    """Persist cleaned Markdown into the document-processing output directory."""

    def __init__(self, output_dir: str | Path = "output") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, markdown: str, source_file_name: str) -> Path:
        output_path = self.output_dir / self._to_markdown_name(source_file_name)
        output_path.write_text(markdown, encoding="utf-8")
        return output_path

    @staticmethod
    def _to_markdown_name(source_file_name: str) -> str:
        stem = Path(source_file_name).stem.strip().lower()
        cleaned = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
        if not cleaned:
            cleaned = "document"
        return f"{cleaned}.md"
