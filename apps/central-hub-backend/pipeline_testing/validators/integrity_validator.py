import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

CHECKS = [
    "no_chunk_gaps", "length_delta", "character_set", "word_coverage",
    "sentence_coverage", "header_coverage", "missing_text",
    "duplicate_text", "integrity_percentage",
]

LENGTH_DELTA_THRESHOLD = 0.25
WORD_INTEGRITY_THRESHOLD = 0.95


@dataclass
class CheckResult:
    check_name: str
    passed: bool
    details: str
    missing_items: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "details": self.details,
            "missing_items": self.missing_items,
        }


@dataclass
class IntegrityReport:
    document_id: str
    original_length: int
    reconstructed_length: int
    passed: bool
    failed_checks: List[str]
    checks: List[CheckResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "original_length": self.original_length,
            "reconstructed_length": self.reconstructed_length,
            "passed": self.passed,
            "failed_checks": self.failed_checks,
            "checks": [c.to_dict() for c in self.checks],
        }


class IntegrityValidator:
    def validate(self, document_id: str, original_text: str,
                 chunks: List[Dict]) -> IntegrityReport:
        reconstructed = "\n\n".join(c.get("text", "") for c in chunks)
        results = []
        for check in CHECKS:
            method = getattr(self, f"_check_{check}")
            results.append(method(original_text, reconstructed, chunks))

        failed = [r.check_name for r in results if not r.passed]
        return IntegrityReport(
            document_id=document_id,
            original_length=len(original_text),
            reconstructed_length=len(reconstructed),
            passed=len(failed) == 0,
            failed_checks=failed,
            checks=results,
        )

    # ------------------------------------------------------------------ #
    #  Check implementations                                               #
    # ------------------------------------------------------------------ #

    def _check_no_chunk_gaps(self, original: str, reconstructed: str,
                              chunks: List[Dict]) -> CheckResult:
        n = len(chunks)
        empty = [i for i, c in enumerate(chunks) if not c.get("text", "").strip()]
        passed = len(empty) == 0
        details = (f"All {n} chunks are non-empty." if passed
                   else f"{len(empty)} empty chunk(s) found.")
        return CheckResult("no_chunk_gaps", passed, details, [str(i) for i in empty])

    def _check_length_delta(self, original: str, reconstructed: str,
                             chunks: List[Dict]) -> CheckResult:
        orig_len = len(original)
        recon_len = len(reconstructed)
        delta = recon_len - orig_len
        pct = (delta / orig_len * 100) if orig_len else 0
        passed = abs(pct / 100) <= LENGTH_DELTA_THRESHOLD
        sign = "+" if delta >= 0 else ""
        details = (f"original={orig_len} chars, reconstructed={recon_len} chars, "
                   f"delta={sign}{delta} ({sign}{pct:.1f}%)")
        return CheckResult("length_delta", passed, details, [])

    def _check_character_set(self, original: str, reconstructed: str,
                              chunks: List[Dict]) -> CheckResult:
        orig_chars = set(original)
        recon_chars = set(reconstructed)
        missing = orig_chars - recon_chars
        passed = len(missing) == 0
        details = ("All characters from original are present in reconstructed text."
                   if passed else f"{len(missing)} character(s) missing.")
        return CheckResult("character_set", passed, details,
                           [repr(c) for c in list(missing)[:10]])

    def _check_word_coverage(self, original: str, reconstructed: str,
                              chunks: List[Dict]) -> CheckResult:
        orig_words = set(re.findall(r"\b\w+\b", original.lower()))
        recon_words = set(re.findall(r"\b\w+\b", reconstructed.lower()))
        missing = orig_words - recon_words
        n = len(orig_words)
        passed = len(missing) == 0
        details = (f"All {n} unique words covered." if passed
                   else f"{len(missing)}/{n} word(s) missing.")
        return CheckResult("word_coverage", passed, details, list(missing)[:10])

    def _check_sentence_coverage(self, original: str, reconstructed: str,
                                  chunks: List[Dict]) -> CheckResult:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", original) if s.strip()]
        if not sentences:
            return CheckResult("sentence_coverage", True, "No sentences found.", [])
        missing = [s for s in sentences if s not in reconstructed]
        n = len(sentences)
        passed = len(missing) == 0
        shown = missing[:10]
        details = (f"All {n} sentences present in reconstructed text." if passed
                   else f"{len(missing)}/{n} sentence(s) missing from reconstructed text "
                        f"(showing up to 10).")
        return CheckResult("sentence_coverage", passed, details, shown)

    def _check_header_coverage(self, original: str, reconstructed: str,
                                chunks: List[Dict]) -> CheckResult:
        headers = re.findall(r"^#{1,6} .+", original, re.MULTILINE)
        if not headers:
            return CheckResult("header_coverage", True,
                               "No ATX headers found in original document.", [])
        missing = [h for h in headers if h not in reconstructed]
        n = len(headers)
        passed = len(missing) == 0
        details = (f"All {n} header(s) present in reconstructed text." if passed
                   else f"{len(missing)}/{n} header(s) missing.")
        return CheckResult("header_coverage", passed, details, missing[:5])

    def _check_missing_text(self, original: str, reconstructed: str,
                             chunks: List[Dict]) -> CheckResult:
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", original) if p.strip()]
        if not paragraphs:
            return CheckResult("missing_text", True, "No paragraphs found.", [])
        missing = [p for p in paragraphs if p not in reconstructed]
        n = len(paragraphs)
        passed = len(missing) == 0
        details = (f"All {n} paragraph(s) present in reconstructed text." if passed
                   else f"{len(missing)}/{n} paragraph(s) missing.")
        return CheckResult("missing_text", passed, details,
                           [p[:80] + "..." for p in missing[:5]])

    def _check_duplicate_text(self, original: str, reconstructed: str,
                               chunks: List[Dict]) -> CheckResult:
        texts = [c.get("text", "").strip() for c in chunks]
        seen: Dict[str, int] = {}
        dupes = []
        for i, t in enumerate(texts):
            if t in seen:
                dupes.append(f"chunk {i} == chunk {seen[t]}")
            else:
                seen[t] = i
        n = len(chunks)
        passed = len(dupes) == 0
        details = (f"No duplicate chunks found across {n} chunk(s)." if passed
                   else f"{len(dupes)} duplicate(s) found.")
        return CheckResult("duplicate_text", passed, details, dupes[:5])

    def _check_integrity_percentage(self, original: str, reconstructed: str,
                                     chunks: List[Dict]) -> CheckResult:
        orig_words = set(re.findall(r"\b\w+\b", original.lower()))
        recon_words = set(re.findall(r"\b\w+\b", reconstructed.lower()))
        n = len(orig_words)
        retained = len(orig_words & recon_words)
        pct = (retained / n * 100) if n else 100.0
        passed = pct >= WORD_INTEGRITY_THRESHOLD * 100
        details = (f"Word integrity: {retained}/{n} unique words retained "
                   f"({pct:.1f}%; threshold {int(WORD_INTEGRITY_THRESHOLD * 100)}%).")
        return CheckResult("integrity_percentage", passed, details, [])
