import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict

logger = logging.getLogger(__name__)


class PipelineTestReporter:
    def __init__(self, json_indent: int = 2):
        self.json_indent = json_indent

    def build_report(self, validation_results: List[Dict],
                     integrity_results: List[Dict],
                     processing_time_s: float) -> Dict:
        total_docs = len(validation_results)
        total_chunks = sum(r.get("total_chunks", 0) for r in validation_results)
        passed_docs = sum(1 for r in validation_results if r.get("passed", False))
        failed_docs = total_docs - passed_docs

        all_rule_results = []
        for doc in validation_results:
            all_rule_results.extend(doc.get("results", []))
        total_validations = len(all_rule_results)
        passed_validations = sum(1 for r in all_rule_results if r.get("passed", False))
        failed_validations = total_validations - passed_validations
        pass_rate = (passed_validations / total_validations) if total_validations else 1.0

        return {
            "run_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "processing_time_s": round(processing_time_s, 3),
            },
            "summary": {
                "documents_processed": total_docs,
                "documents_passed": passed_docs,
                "documents_failed": failed_docs,
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "failed_validations": failed_validations,
                "validation_pass_rate": round(pass_rate, 4),
            },
            "validation_results": validation_results,
            "integrity_results": integrity_results,
        }

    def save(self, report: Dict, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=self.json_indent, ensure_ascii=False)
        logger.info("Saved pipeline test report → %s", path)

    def print_summary(self, report: Dict) -> None:
        meta = report["run_metadata"]
        summ = report["summary"]
        print(f"\n{'='*60}")
        print(f"Pipeline Test Report — {meta['timestamp']}")
        print(f"{'='*60}")
        print(f"Documents : {summ['documents_processed']} processed, "
              f"{summ['documents_passed']} passed, {summ['documents_failed']} failed")
        print(f"Chunks    : {meta['total_chunks']}")
        print(f"Validations: {summ['passed_validations']}/{summ['total_validations']} passed "
              f"({summ['validation_pass_rate']*100:.1f}%)")
        print(f"Time      : {meta['processing_time_s']}s")

        failed_integrity = [r["document_id"] for r in report.get("integrity_results", [])
                            if not r.get("passed", True)]
        if failed_integrity:
            print(f"\nIntegrity failures ({len(failed_integrity)}): "
                  f"{', '.join(failed_integrity[:10])}")
        print(f"{'='*60}\n")
