"""Run text extraction for a single document path."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from extractors.extractor_factory import ExtractorFactory


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract raw text from a document.")
    parser.add_argument("file_path", help="Path to a PDF, DOCX, or TXT file.")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    extractor = ExtractorFactory.create(file_path)
    result = extractor.extract(file_path)

    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
