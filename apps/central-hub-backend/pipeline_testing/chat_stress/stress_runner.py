"""
Asynchronous Stress Runner for the live RAG chat endpoint.

Fires concurrent HTTP requests to /api/v1/bots/retrieve, records per-request
metrics, detects SSE streaming responses, and computes aggregate statistics.

Usage
-----
    import asyncio
    from pipeline_testing.chat_stress.query_generator import SyntheticChatQueryGenerator
    from pipeline_testing.chat_stress.stress_runner import StressRunner, StressConfig

    gen = SyntheticChatQueryGenerator(seed=42, platform_id="tensor")
    queries = gen.generate_all(total=100)

    cfg = StressConfig(
        base_url="http://localhost:8000",
        api_token="your_bearer_token",
        bot_id="your-bot-uuid",
        concurrency=10,
        timeout=30.0,
        max_retries=2,
    )
    runner = StressRunner(cfg)
    results, stats = asyncio.run(runner.run(queries))
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional httpx import — graceful degradation when not installed
# ---------------------------------------------------------------------------
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HTTPX_AVAILABLE = False
    logger.warning(
        "httpx is not installed. Install it with: pip install httpx\n"
        "StressRunner will raise RuntimeError if executed without httpx."
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class StressConfig:
    """
    Configuration for the stress runner.

    Mirrors the style of PipelineTestConfig / GeneratorConfig in config.py.
    """
    base_url: str = "http://localhost:8000"
    api_token: str = ""                    # Bearer token for authentication
    bot_id: str = ""                       # UUID of the bot to query
    concurrency: int = 10                  # max simultaneous requests
    total_requests: Optional[int] = None   # cap; None → use all supplied queries
    timeout: float = 30.0                  # per-request timeout in seconds
    max_retries: int = 2                   # retries on transient (5xx / network) errors
    retry_delay: float = 0.5              # seconds between retries
    conversation_id_prefix: str = "stress"
    detect_streaming: bool = True          # attempt SSE detection


@dataclass
class RequestResult:
    """Outcome of a single HTTP request."""
    request_id: str
    query_id: str
    category: str
    query_text: str
    status_code: int
    response_time_ms: float
    success: bool
    response_length: int
    error_message: str
    is_streaming: bool
    streaming_complete: bool
    fallback_triggered: bool
    platform_id_in_response: str
    attempt: int                           # which retry attempt succeeded (1-based)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "query_id": self.query_id,
            "category": self.category,
            "query_text": self.query_text[:120],   # truncate for readability
            "status_code": self.status_code,
            "response_time_ms": round(self.response_time_ms, 3),
            "success": self.success,
            "response_length": self.response_length,
            "error_message": self.error_message,
            "is_streaming": self.is_streaming,
            "streaming_complete": self.streaming_complete,
            "fallback_triggered": self.fallback_triggered,
            "platform_id_in_response": self.platform_id_in_response,
            "attempt": self.attempt,
        }


@dataclass
class AggregateStats:
    """Computed statistics over all RequestResult objects."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    throughput_rps: float = 0.0            # requests per second
    total_wall_time_s: float = 0.0
    streaming_requests: int = 0
    streaming_complete: int = 0
    fallback_triggered: int = 0
    platform_isolation_violations: int = 0  # responses with wrong platform_id
    per_category: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 4),
            "error_rate": round(self.error_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 3),
            "min_latency_ms": round(self.min_latency_ms, 3),
            "max_latency_ms": round(self.max_latency_ms, 3),
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "p99_ms": round(self.p99_ms, 3),
            "throughput_rps": round(self.throughput_rps, 4),
            "total_wall_time_s": round(self.total_wall_time_s, 3),
            "streaming_requests": self.streaming_requests,
            "streaming_complete": self.streaming_complete,
            "fallback_triggered": self.fallback_triggered,
            "platform_isolation_violations": self.platform_isolation_violations,
            "per_category": self.per_category,
        }


# ---------------------------------------------------------------------------
# Percentile helper (stdlib only — no numpy dependency)
# ---------------------------------------------------------------------------

def _percentile(sorted_values: List[float], pct: float) -> float:
    """Return the *pct*-th percentile of a pre-sorted list."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * pct / 100.0
    lo = int(k)
    hi = lo + 1
    if hi >= len(sorted_values):
        return sorted_values[-1]
    frac = k - lo
    return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])


# ---------------------------------------------------------------------------
# StressRunner
# ---------------------------------------------------------------------------

class StressRunner:
    """
    Fires concurrent HTTP requests to the live RAG endpoint and collects metrics.

    Parameters
    ----------
    config : StressConfig
        Runtime configuration (URL, token, concurrency, etc.).
    expected_platform_id : str, optional
        When set, every response is checked to ensure its platform_id matches.
        Mismatches are counted as platform isolation violations.
    """

    def __init__(
        self,
        config: StressConfig,
        expected_platform_id: Optional[str] = None,
    ) -> None:
        self.config = config
        self.expected_platform_id = expected_platform_id

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(
        self,
        queries,   # List[ChatQuery] | List[MultiTurnConversation] — duck typing
    ) -> Tuple[List[RequestResult], AggregateStats]:
        """
        Execute the stress test.

        Parameters
        ----------
        queries : list of ChatQuery or MultiTurnConversation
            Queries to fire.  Both flat ``ChatQuery`` objects and
            ``MultiTurnConversation`` objects are accepted.  If
            config.total_requests is set, the list is truncated / repeated to
            match that count.

        Returns
        -------
        results : list of RequestResult
        stats   : AggregateStats
        """
        if not _HTTPX_AVAILABLE:
            raise RuntimeError(
                "httpx is required for StressRunner. "
                "Install it with: pip install httpx"
            )

        work = self._prepare_work(queries)
        logger.info(
            "Starting stress test: %d requests, concurrency=%d, timeout=%.1fs",
            len(work), self.config.concurrency, self.config.timeout,
        )

        semaphore = asyncio.Semaphore(self.config.concurrency)
        wall_start = time.perf_counter()

        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=self._auth_headers(),
        ) as client:
            tasks = [
                self._bounded_request(client, semaphore, query)
                for query in work
            ]
            results: List[RequestResult] = await asyncio.gather(*tasks)

        wall_time = time.perf_counter() - wall_start
        stats = self._compute_stats(results, wall_time)

        logger.info(
            "Stress test complete: %d/%d succeeded (%.1f%%), "
            "avg=%.1fms, p95=%.1fms, throughput=%.2f rps",
            stats.successful_requests, stats.total_requests,
            stats.success_rate * 100,
            stats.avg_latency_ms, stats.p95_ms, stats.throughput_rps,
        )
        return results, stats

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare_work(self, queries) -> list:
        """Truncate or cycle the query list to match config.total_requests."""
        if not queries:
            return []
        cap = self.config.total_requests
        if cap is None:
            return list(queries)
        if cap <= len(queries):
            return list(queries[:cap])
        # Repeat the list to fill the requested count
        repeated = []
        while len(repeated) < cap:
            repeated.extend(queries)
        return repeated[:cap]

    def _auth_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        return headers

    async def _bounded_request(
        self,
        client,
        semaphore: asyncio.Semaphore,
        query,
    ) -> RequestResult:
        async with semaphore:
            return await self._execute_with_retry(client, query)

    async def _execute_with_retry(self, client, query) -> RequestResult:
        """Execute a single request, retrying on transient failures."""
        last_result: Optional[RequestResult] = None
        for attempt in range(1, self.config.max_retries + 2):  # +2: 1 initial + N retries
            result = await self._single_request(client, query, attempt)
            last_result = result
            if result.success or not self._is_retryable(result):
                return result
            if attempt <= self.config.max_retries:
                logger.debug(
                    "Retrying query %s (attempt %d/%d) after status %d",
                    query.query_id, attempt, self.config.max_retries + 1,
                    result.status_code,
                )
                await asyncio.sleep(self.config.retry_delay)
        return last_result  # type: ignore[return-value]

    @staticmethod
    def _is_retryable(result: RequestResult) -> bool:
        """5xx errors and network errors are retryable; 4xx are not."""
        if result.status_code == 0:   # network / timeout error
            return True
        return result.status_code >= 500

    async def _single_request(
        self,
        client,
        query,
        attempt: int,
    ) -> RequestResult:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        conversation_id = f"{self.config.conversation_id_prefix}_{uuid.uuid4().hex[:8]}"

        payload = {
            "query": query.text,
            "conversation_id": conversation_id,
        }
        if self.config.bot_id:
            payload["bot_id"] = self.config.bot_id

        # Multi-turn: if the item exposes a chat_history property, include it
        chat_history = getattr(query, "chat_history", None)
        if chat_history:
            payload["chat_history"] = chat_history

        # Multi-turn: resolve the actual query text from MultiTurnConversation
        query_text = getattr(query, "final_query", None) or getattr(query, "text", "")
        payload["query"] = query_text

        status_code = 0
        response_time_ms = 0.0
        response_length = 0
        error_message = ""
        is_streaming = False
        streaming_complete = False
        fallback_triggered = False
        platform_id_in_response = ""
        success = False

        t0 = time.perf_counter()
        try:
            response = await client.post("/api/v1/bots/retrieve", json=payload)
            response_time_ms = (time.perf_counter() - t0) * 1000.0
            status_code = response.status_code
            response_length = len(response.content)

            # Detect SSE streaming
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                is_streaming = True
                streaming_complete = self._validate_sse(response.text)
            else:
                # JSON response
                try:
                    body = response.json()
                    fallback_triggered = bool(body.get("fallback_triggered", False))
                    platform_id_in_response = str(body.get("platform_id", ""))
                except Exception:
                    pass

            success = 200 <= status_code < 300

        except httpx.TimeoutException as exc:
            response_time_ms = (time.perf_counter() - t0) * 1000.0
            error_message = f"Timeout: {exc}"
            logger.debug("Request %s timed out: %s", request_id, exc)

        except httpx.RequestError as exc:
            response_time_ms = (time.perf_counter() - t0) * 1000.0
            error_message = f"RequestError: {exc}"
            logger.debug("Request %s network error: %s", request_id, exc)

        except Exception as exc:
            response_time_ms = (time.perf_counter() - t0) * 1000.0
            error_message = f"Unexpected: {exc}"
            logger.debug("Request %s unexpected error: %s", request_id, exc)

        return RequestResult(
            request_id=request_id,
            query_id=query.query_id,
            category=query.category if isinstance(query.category, str) else query.category.value,
            query_text=query.text,
            status_code=status_code,
            response_time_ms=response_time_ms,
            success=success,
            response_length=response_length,
            error_message=error_message,
            is_streaming=is_streaming,
            streaming_complete=streaming_complete,
            fallback_triggered=fallback_triggered,
            platform_id_in_response=platform_id_in_response,
            attempt=attempt,
        )

    @staticmethod
    def _validate_sse(body: str) -> bool:
        """
        Validate that an SSE response body is well-formed.

        A valid SSE stream must contain at least one 'data:' line and end with
        the conventional '[DONE]' sentinel or a double newline terminator.
        """
        if not body:
            return False
        lines = body.splitlines()
        has_data = any(line.startswith("data:") for line in lines)
        has_done = "[DONE]" in body or body.rstrip().endswith("\n\n")
        return has_data and has_done

    def _compute_stats(
        self,
        results: List[RequestResult],
        wall_time: float,
    ) -> AggregateStats:
        stats = AggregateStats()
        stats.total_requests = len(results)
        stats.total_wall_time_s = wall_time

        if not results:
            return stats

        latencies = sorted(r.response_time_ms for r in results)
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        stats.successful_requests = len(successful)
        stats.failed_requests = len(failed)
        stats.success_rate = len(successful) / len(results)
        stats.error_rate = len(failed) / len(results)

        stats.avg_latency_ms = sum(latencies) / len(latencies)
        stats.min_latency_ms = latencies[0]
        stats.max_latency_ms = latencies[-1]
        stats.p50_ms = _percentile(latencies, 50)
        stats.p95_ms = _percentile(latencies, 95)
        stats.p99_ms = _percentile(latencies, 99)

        stats.throughput_rps = len(results) / wall_time if wall_time > 0 else 0.0

        stats.streaming_requests = sum(1 for r in results if r.is_streaming)
        stats.streaming_complete = sum(1 for r in results if r.streaming_complete)
        stats.fallback_triggered = sum(1 for r in results if r.fallback_triggered)

        # Platform isolation: count responses where platform_id doesn't match expected
        if self.expected_platform_id:
            stats.platform_isolation_violations = sum(
                1 for r in results
                if r.success
                and r.platform_id_in_response
                and r.platform_id_in_response != self.expected_platform_id
            )

        # Per-category breakdown
        categories: dict = {}
        for r in results:
            cat = r.category
            if cat not in categories:
                categories[cat] = {
                    "total": 0, "success": 0, "failure": 0,
                    "fallback": 0, "latencies": [],
                }
            categories[cat]["total"] += 1
            if r.success:
                categories[cat]["success"] += 1
            else:
                categories[cat]["failure"] += 1
            if r.fallback_triggered:
                categories[cat]["fallback"] += 1
            categories[cat]["latencies"].append(r.response_time_ms)

        for cat, data in categories.items():
            lats = sorted(data.pop("latencies"))
            stats.per_category[cat] = {
                **data,
                "avg_latency_ms": round(sum(lats) / len(lats), 3) if lats else 0.0,
                "p95_ms": round(_percentile(lats, 95), 3),
            }

        return stats
