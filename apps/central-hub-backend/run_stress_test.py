"""
Chat Stress-Test CLI — entry point.

Fires synthetic chat queries against the live RAG endpoint and produces a
JSON report in pipeline_testing/outputs/stress_test_report.json.

Usage
-----
    # Minimal (server must be running locally)
    python run_stress_test.py --token YOUR_BEARER_TOKEN --bot-id YOUR_BOT_UUID

    # Full options
    python run_stress_test.py \\
        --base-url http://localhost:8000 \\
        --token    YOUR_BEARER_TOKEN     \\
        --bot-id   YOUR_BOT_UUID         \\
        --total    200                   \\
        --concurrency 20                 \\
        --timeout  30                    \\
        --seed     42                    \\
        --platform tensor                \\
        --categories in_domain out_of_context adversarial

    # Multi-turn conversation stress test
    python run_stress_test.py --multi-turn --turns 4 --total 50 --token TOKEN --bot-id UUID

    # Dry-run: generate queries only, do not fire HTTP requests
    python run_stress_test.py --dry-run --total 50
"""

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline_testing.chat_stress.query_generator import (
    SyntheticChatQueryGenerator,
    QueryCategory,
    MultiTurnConversation,
)
from pipeline_testing.chat_stress.stress_runner import StressRunner, StressConfig
from pipeline_testing.chat_stress.latency_reporter import LatencyReporter
from pipeline_testing.config import OUTPUTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_ALL_CATEGORIES = [c.value for c in QueryCategory]


def _parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Synthetic chat stress-test for the live RAG pipeline"
    )
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="Base URL of the running backend (default: http://localhost:8000)")
    parser.add_argument("--token", default="",
                        help="Bearer token for authentication")
    parser.add_argument("--bot-id", default="",
                        help="UUID of the bot to query")
    parser.add_argument("--total", type=int, default=100,
                        help="Total number of requests to fire (default: 100)")
    parser.add_argument("--concurrency", type=int, default=10,
                        help="Maximum simultaneous requests (default: 10)")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="Per-request timeout in seconds (default: 30)")
    parser.add_argument("--retries", type=int, default=2,
                        help="Retries on transient failures (default: 2)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for query generation (default: 42)")
    parser.add_argument("--platform", default="test_platform",
                        help="Platform/tenant ID stamped on queries (default: test_platform)")
    parser.add_argument("--categories", nargs="+", default=None,
                        choices=_ALL_CATEGORIES,
                        help="Restrict to specific query categories")
    parser.add_argument("--multi-turn", action="store_true",
                        help="Generate multi-turn conversations instead of flat queries")
    parser.add_argument("--turns", type=int, default=3,
                        help="User turns per conversation when --multi-turn is set (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate queries but do not fire HTTP requests")
    parser.add_argument("--output", default=None,
                        help="Override output filename (default: stress_test_report.json)")
    return parser.parse_args(args)


async def _run(opts) -> dict:
    gen = SyntheticChatQueryGenerator(seed=opts.seed, platform_id=opts.platform)

    # ── 1. Generate synthetic queries or multi-turn conversations ────────
    if opts.multi_turn:
        queries = gen.generate_multi_turn_conversations(
            total_conversations=opts.total,
            turns_per_conversation=opts.turns,
        )
        logger.info(
            "Generated %d multi-turn conversations (%d user turns each)",
            len(queries), opts.turns,
        )
    elif opts.categories:
        queries = []
        per_cat = max(1, opts.total // len(opts.categories))
        for cat in opts.categories:
            queries.extend(gen.generate_category(QueryCategory(cat), count=per_cat))
        queries = queries[: opts.total]
        logger.info("Generated %d synthetic chat queries", len(queries))
    else:
        queries = gen.generate_all(total=opts.total)
        logger.info("Generated %d synthetic chat queries", len(queries))

    if opts.dry_run:
        logger.info("Dry-run mode — skipping HTTP requests")
        from pipeline_testing.chat_stress.stress_runner import AggregateStats
        stats = AggregateStats(total_requests=len(queries))
        reporter = LatencyReporter(json_indent=2)
        report = reporter.build_report([], stats, queries)
        report["dry_run"] = True
        report["multi_turn"] = opts.multi_turn
        report["generated_queries"] = [q.to_dict() for q in queries]
        filename = opts.output or "stress_test_report.json"
        reporter.save(report, filename)
        reporter.print_summary(report)
        return report

    # ── 2. Configure and run the stress test ─────────────────────────────
    cfg = StressConfig(
        base_url=opts.base_url,
        api_token=opts.token,
        bot_id=opts.bot_id,
        concurrency=opts.concurrency,
        total_requests=opts.total,
        timeout=opts.timeout,
        max_retries=opts.retries,
    )
    runner = StressRunner(cfg, expected_platform_id=opts.platform or None)
    results, stats = await runner.run(queries)

    # ── 3. Build and save the report ─────────────────────────────────────
    reporter = LatencyReporter(config=cfg, json_indent=2)
    report = reporter.build_report(results, stats, queries)
    report["multi_turn"] = opts.multi_turn
    filename = opts.output or "stress_test_report.json"
    reporter.save(report, filename)
    reporter.print_summary(report)
    return report


def run(args=None):
    opts = _parse_args(args)
    return asyncio.run(_run(opts))


if __name__ == "__main__":
    run()
