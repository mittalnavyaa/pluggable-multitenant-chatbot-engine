import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

RULES = [
    "empty_chunks", "chunk_size", "chunk_overlap", "duplicate_chunks",
    "page_number_validation", "max_chunk_size", "min_chunk_size",
    "header_preservation", "markdown_preservation", "table_preservation",
    "code_block_preservation", "list_preservation", "unicode_preservation",
]


@dataclass
class RuleResult:
    rule: str
    passed: bool
    failure_count: int
    failures: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "passed": self.passed,
            "failure_count": self.failure_count,
            "failures": self.failures,
        }


@dataclass
class DocumentValidationReport:
    document_id: str
    total_chunks: int
    passed: bool
    failed_rules: List[str]
    results: List[RuleResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "total_chunks": self.total_chunks,
            "passed": self.passed,
            "failed_rules": self.failed_rules,
            "results": [r.to_dict() for r in self.results],
        }


class ChunkValidator:
    def __init__(self, max_chunk_size: int = 1200, min_chunk_size: int = 10,
                 chunk_size: int = 1000, chunk_overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def validate(self, document_id: str, original_text: str,
                 chunks: List[Dict]) -> DocumentValidationReport:
        results = []
        for rule in RULES:
            method = getattr(self, f"_check_{rule}")
            results.append(method(original_text, chunks))

        failed_rules = [r.rule for r in results if not r.passed]
        return DocumentValidationReport(
            document_id=document_id,
            total_chunks=len(chunks),
            passed=len(failed_rules) == 0,
            failed_rules=failed_rules,
            results=results,
        )

    # ------------------------------------------------------------------ #
    #  Rule implementations                                                #
    # ------------------------------------------------------------------ #

    def _check_empty_chunks(self, original: str, chunks: List[Dict]) -> RuleResult:
        failures = [str(i) for i, c in enumerate(chunks) if not c.get("text", "").strip()]
        return RuleResult("empty_chunks", len(failures) == 0, len(failures), failures)

    def _check_chunk_size(self, original: str, chunks: List[Dict]) -> RuleResult:
        failures = []
        for i, c in enumerate(chunks):
            size = len(c.get("text", ""))
            if size > self.chunk_size * 1.5:
                failures.append(f"chunk {i}: {size} chars")
        return RuleResult("chunk_size", len(failures) == 0, len(failures), failures)

    def _check_chunk_overlap(self, original: str, chunks: List[Dict]) -> RuleResult:
        failures = []
        texts = [c.get("text", "") for c in chunks]
        for i in range(1, len(texts)):
            prev, curr = texts[i - 1], texts[i]
            if len(prev) >= self.chunk_overlap and len(curr) >= self.chunk_overlap:
                tail = prev[-self.chunk_overlap:]
                if tail and tail not in curr and not any(
                    w in curr for w in tail.split()[-3:]
                ):
                    failures.append(f"chunk {i}: no overlap detected")
        return RuleResult("chunk_overlap", len(failures) == 0, len(failures), failures)

    def _check_duplicate_chunks(self, original: str, chunks: List[Dict]) -> RuleResult:
        seen: Dict[str, int] = {}
        failures = []
        for i, c in enumerate(chunks):
            text = c.get("text", "").strip()
            if text in seen:
                failures.append(f"chunk {i} duplicates chunk {seen[text]}")
            else:
                seen[text] = i
        return RuleResult("duplicate_chunks", len(failures) == 0, len(failures), failures)

    def _check_page_number_validation(self, original: str, chunks: List[Dict]) -> RuleResult:
        failures = []
        for i, c in enumerate(chunks):
            pn = c.get("page_number")
            if pn is None or not isinstance(pn, int) or pn < 1:
                failures.append(f"chunk {i}: invalid page_number={pn!r}")
        return RuleResult("page_number_validation", len(failures) == 0, len(failures), failures)

    def _check_max_chunk_size(self, original: str, chunks: List[Dict]) -> RuleResult:
        failures = []
        for i, c in enumerate(chunks):
            size = len(c.get("text", ""))
            if size > self.max_chunk_size:
                failures.append(f"chunk {i}: {size} > {self.max_chunk_size}")
        return RuleResult("max_chunk_size", len(failures) == 0, len(failures), failures)

    def _check_min_chunk_size(self, original: str, chunks: List[Dict]) -> RuleResult:
        failures = []
        for i, c in enumerate(chunks):
            size = len(c.get("text", "").strip())
            if size < self.min_chunk_size:
                failures.append(f"chunk {i}: {size} < {self.min_chunk_size}")
        return RuleResult("min_chunk_size", len(failures) == 0, len(failures), failures)

    def _check_header_preservation(self, original: str, chunks: List[Dict]) -> RuleResult:
        headers = re.findall(r"^#{1,6} .+", original, re.MULTILINE)
        if not headers:
            return RuleResult("header_preservation", True, 0, [])
        all_text = "\n".join(c.get("text", "") for c in chunks)
        missing = [h for h in headers if h not in all_text]
        return RuleResult("header_preservation", len(missing) == 0, len(missing), missing[:5])

    def _check_markdown_preservation(self, original: str, chunks: List[Dict]) -> RuleResult:
        bold = re.findall(r"\*\*[^*]+\*\*", original)
        code_inline = re.findall(r"`[^`]+`", original)
        all_text = "\n".join(c.get("text", "") for c in chunks)
        missing = [m for m in bold + code_inline if m not in all_text]
        return RuleResult("markdown_preservation", len(missing) == 0, len(missing), missing[:5])

    def _check_table_preservation(self, original: str, chunks: List[Dict]) -> RuleResult:
        table_rows = re.findall(r"^\|.+\|$", original, re.MULTILINE)
        if not table_rows:
            return RuleResult("table_preservation", True, 0, [])
        all_text = "\n".join(c.get("text", "") for c in chunks)
        missing = [r for r in table_rows if r not in all_text]
        return RuleResult("table_preservation", len(missing) == 0, len(missing), missing[:3])

    def _check_code_block_preservation(self, original: str, chunks: List[Dict]) -> RuleResult:
        blocks = re.findall(r"```[\s\S]*?```", original)
        if not blocks:
            return RuleResult("code_block_preservation", True, 0, [])
        all_text = "\n".join(c.get("text", "") for c in chunks)
        missing = [b[:60] + "..." for b in blocks if b not in all_text]
        return RuleResult("code_block_preservation", len(missing) == 0, len(missing), missing[:3])

    def _check_list_preservation(self, original: str, chunks: List[Dict]) -> RuleResult:
        list_items = re.findall(r"^[-*] .+|^\d+\. .+", original, re.MULTILINE)
        if not list_items:
            return RuleResult("list_preservation", True, 0, [])
        all_text = "\n".join(c.get("text", "") for c in chunks)
        missing = [item for item in list_items if item not in all_text]
        return RuleResult("list_preservation", len(missing) == 0, len(missing), missing[:5])

    def _check_unicode_preservation(self, original: str, chunks: List[Dict]) -> RuleResult:
        non_ascii = set(ch for ch in original if ord(ch) > 127)
        if not non_ascii:
            return RuleResult("unicode_preservation", True, 0, [])
        all_text = "\n".join(c.get("text", "") for c in chunks)
        missing = [ch for ch in non_ascii if ch not in all_text]
        return RuleResult("unicode_preservation", len(missing) == 0, len(missing),
                          [repr(ch) for ch in missing[:10]])
