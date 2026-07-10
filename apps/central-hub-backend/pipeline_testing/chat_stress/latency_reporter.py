"""
Latency Reporter for the Chat Stress Test.

Builds a structured JSON report from StressRunner results and saves it to
pipeline_testing/outputs/stress_test_report.json.

Reuses OUTPUTS_DIR from the existing pipeline_testing.config module so the
report lands in the same directory as pipeline_test_report.json.

Usage
-----
    from pipeline_testing.chat_stress.latency_reporter import LatencyReporter
    from pipeline_testing.chat_stress.stress_runner import StressConfig

    reporter = LatencyReporter(config=cfg)
    report = reporter.build_report(results, stats, queries)
    reporter.save(report)
    reporter.print_summary(report)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

# Reuse the outputs directory defined in the existing config module
try:
    from pipeline_testing.config import OUTPUTS_DIR
except ImportError:
    # Fallback: resolve relative to this file's location
    OUTPUTS_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "outputs",
    )

_REPORT_FILENAME = "stress_test_report.json"
_TOP_N = 10   # number of slowest / failed requests to surface in the report


class LatencyReporter:
    """
    Builds and persists the stress-test report.

    Parameters
    ----------
    config : StressConfig, optional
        The StressConfig used for the run.  When supplied, its fields are
        embedded in the report under ``test_configuration``.
    json_indent : int
        JSON indentation level (mirrors PipelineTestReporter).
    output_dir : str, optional
        Override the output directory.  Defaults to OUTPUTS_DIR from config.py.
    """

    def __init__(
        self,
        config=None,
        json_indent: int = 2,
        output_dir: Optional[str] = None,
    ) -> None:
        self.config = config
        self.json_indent = json_indent
        self.output_dir = output_dir or OUTPUTS_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_report(
        self,
        results,        # List[RequestResult]
        stats,          # AggregateStats
        queries=None,   # List[ChatQuery] — optional, used for category summary
    ) -> dict:
        """
        Assemble the full report dictionary.

        Parameters
        ----------
        results : list of RequestResult
        stats   : AggregateStats
        queries : list of ChatQuery, optional

        Returns
        -------
        dict — the complete report, ready for JSON serialisation.
        """
        report = {
            "run_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "report_version": "1.0.0",
                "generator": "pipeline_testing.chat_stress.LatencyReporter",
            },
            "test_configuration": self._serialise_config(),
            "summary": self._build_summary(stats),
            "latency_distribution": {
                "avg_ms": round(stats.avg_latency_ms, 3),
                "min_ms": round(stats.min_latency_ms, 3),
                "max_ms": round(stats.max_latency_ms, 3),
                "p50_ms": round(stats.p50_ms, 3),
                "p95_ms": round(stats.p95_ms, 3),
                "p99_ms": round(stats.p99_ms, 3),
            },
            "platform_isolation_validation": self._build_isolation_summary(stats),
            "streaming_validation": self._build_streaming_summary(stats),
            "per_category_breakdown": stats.per_category,
            "top_slowest_requests": self._top_slowest(results),
            "top_failed_requests": self._top_failed(results),
        }
        return report

    def save(self, report: dict, filename: str = _REPORT_FILENAME) -> str:
        """
        Persist the report to disk.

        Returns the absolute path of the saved file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=self.json_indent, ensure_ascii=False)
        logger.info("Saved stress test report → %s", path)
        return path

    def print_summary(self, report: dict) -> None:
        """Print a human-readable summary to stdout (mirrors PipelineTestReporter)."""
        meta = report["run_metadata"]
        summ = report["summary"]
        lat = report["latency_distribution"]
        iso = report["platform_isolation_validation"]
        stream = report["streaming_validation"]

        print(f"\n{'=' * 65}")
        print(f"Chat Stress Test Report — {meta['timestamp']}")
        print(f"{'=' * 65}")
        print(
            f"Requests  : {summ['total_requests']} total, "
            f"{summ['successful_requests']} succeeded, "
            f"{summ['failed_requests']} failed"
        )
        print(
            f"Success   : {summ['success_percentage']:.1f}%   "
            f"Error: {summ['error_percentage']:.1f}%"
        )
        print(
            f"Latency   : avg={lat['avg_ms']}ms  "
            f"p50={lat['p50_ms']}ms  "
            f"p95={lat['p95_ms']}ms  "
            f"p99={lat['p99_ms']}ms"
        )
        print(
            f"Throughput: {summ['throughput_rps']:.2f} req/s  "
            f"(wall time {summ['total_wall_time_s']:.2f}s)"
        )
        print(
            f"Fallbacks : {summ['fallback_triggered']}  "
            f"Isolation violations: {iso['violations']}"
        )
        if stream["total_streaming_requests"] > 0:
            print(
                f"Streaming : {stream['streaming_complete']}/{stream['total_streaming_requests']} "
                f"completed ({stream['streaming_success_rate'] * 100:.1f}%)"
            )
        print(f"{'=' * 65}\n")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _serialise_config(self) -> dict:
        if self.config is None:
            return {}
        cfg = self.config
        return {
            "base_url": getattr(cfg, "base_url", ""),
            "concurrency": getattr(cfg, "concurrency", None),
            "total_requests": getattr(cfg, "total_requests", None),
            "timeout_s": getattr(cfg, "timeout", None),
            "max_retries": getattr(cfg, "max_retries", None),
            "detect_streaming": getattr(cfg, "detect_streaming", None),
        }

    @staticmethod
    def _build_summary(stats) -> dict:
        return {
            "total_requests": stats.total_requests,
            "successful_requests": stats.successful_requests,
            "failed_requests": stats.failed_requests,
            "success_percentage": round(stats.success_rate * 100, 2),
            "error_percentage": round(stats.error_rate * 100, 2),
            "throughput_rps": round(stats.throughput_rps, 4),
            "total_wall_time_s": round(stats.total_wall_time_s, 3),
            "fallback_triggered": stats.fallback_triggered,
        }

    @staticmethod
    def _build_isolation_summary(stats) -> dict:
        return {
            "violations": stats.platform_isolation_violations,
            "passed": stats.platform_isolation_violations == 0,
            "note": (
                "All responses returned the expected platform_id."
                if stats.platform_isolation_violations == 0
                else (
                    f"{stats.platform_isolation_violations} response(s) contained "
                    "a platform_id that did not match the expected tenant."
                )
            ),
        }

    @staticmethod
    def _build_streaming_summary(stats) -> dict:
        total = stats.streaming_requests
        complete = stats.streaming_complete
        rate = (complete / total) if total > 0 else 1.0
        return {
            "total_streaming_requests": total,
            "streaming_complete": complete,
            "streaming_success_rate": round(rate, 4),
            "passed": total == 0 or rate == 1.0,
        }

    @staticmethod
    def _top_slowest(results, n: int = _TOP_N) -> List[dict]:
        sorted_results = sorted(results, key=lambda r: r.response_time_ms, reverse=True)
        return [r.to_dict() for r in sorted_results[:n]]

    @staticmethod
    def _top_failed(results, n: int = _TOP_N) -> List[dict]:
        failed = [r for r in results if not r.success]
        return [r.to_dict() for r in failed[:n]]
