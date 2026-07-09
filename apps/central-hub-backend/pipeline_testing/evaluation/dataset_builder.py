import csv
import json
import logging
import os
from typing import Dict, List

from .question_generator import EvaluationQuestionGenerator

logger = logging.getLogger(__name__)


class EvaluationDatasetBuilder:
    def __init__(self, question_generator: EvaluationQuestionGenerator = None,
                 max_chunks_per_doc: int = 5):
        self.question_generator = question_generator
        self.max_chunks_per_doc = max_chunks_per_doc
        self._records: List[Dict] = []

    def add_document(self, document_id: str, document_type: str,
                     source_file: str, chunks: List[Dict]) -> None:
        selected = chunks[: self.max_chunks_per_doc]
        for idx, chunk in enumerate(selected):
            text = chunk.get("text", "")
            questions = []
            if self.question_generator:
                try:
                    questions = self.question_generator.generate(text)
                except Exception as exc:
                    logger.warning("Question gen failed for %s chunk %d: %s",
                                   document_id, idx, exc)
            self._records.append({
                "document_id": document_id,
                "document_type": document_type,
                "source_file": source_file,
                "chunk_index": idx,
                "chunk_text": text,
                "chunk_metadata": {
                    "page_number": chunk.get("page_number", 1),
                    "char_length": len(text),
                },
                "questions": questions,
                "expected_chunk_id": idx,
            })

    def save_json(self, path: str, indent: int = 2) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=indent, ensure_ascii=False)
        logger.info("Saved evaluation dataset JSON → %s (%d records)",
                    path, len(self._records))

    def save_csv(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not self._records:
            return
        fieldnames = ["document_id", "document_type", "source_file",
                      "chunk_index", "chunk_text", "page_number",
                      "char_length", "questions", "expected_chunk_id"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self._records:
                writer.writerow({
                    "document_id": r["document_id"],
                    "document_type": r["document_type"],
                    "source_file": r["source_file"],
                    "chunk_index": r["chunk_index"],
                    "chunk_text": r["chunk_text"],
                    "page_number": r["chunk_metadata"]["page_number"],
                    "char_length": r["chunk_metadata"]["char_length"],
                    "questions": "|".join(r["questions"]),
                    "expected_chunk_id": r["expected_chunk_id"],
                })
        logger.info("Saved evaluation dataset CSV → %s", path)

    @property
    def records(self) -> List[Dict]:
        return self._records
