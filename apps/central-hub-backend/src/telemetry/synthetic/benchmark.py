# apps/central-hub-backend/src/telemetry/synthetic/benchmark.py

import sys
import os
import time
import tracemalloc
from typing import Dict, Any

# Resolve path relative to central-hub-backend root
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.telemetry.synthetic.config import GeneratorConfig
from src.telemetry.synthetic.generator import SyntheticTelemetryGenerator

def run_single_benchmark(count: int) -> Dict[str, Any]:
    """Runs generation benchmark for a specific count of events."""
    tracemalloc.start()
    
    # Configure generator
    config = GeneratorConfig(
        total_conversations=count,
        random_seed=42,
        use_llm=False
    )
    
    start_time = time.perf_counter()
    generator = SyntheticTelemetryGenerator(config)
    data = generator.generate()
    end_time = time.perf_counter()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration = end_time - start_time
    throughput = count / duration if duration > 0 else 0
    
    return {
        "count": count,
        "duration_seconds": round(duration, 4),
        "throughput_eps": round(throughput, 2),
        "peak_memory_mb": round(peak / (1024 * 1024), 2),
        "current_memory_mb": round(current / (1024 * 1024), 2)
    }

def main() -> None:
    print("=" * 60)
    print("ENVOY AI: SYNTHETIC TELEMETRY GENERATION PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Run benchmark for 1,000 conversations
    print("\nRunning benchmark: 1,000 conversations...")
    results_1k = run_single_benchmark(1000)
    
    # Run benchmark for 10,000 conversations
    print("Running benchmark: 10,000 conversations...")
    results_10k = run_single_benchmark(10000)
    
    # Output formatting
    print("\n" + "=" * 60)
    print(f"{'Metric':<25} | {'1,000 Events':<15} | {'10,000 Events':<15}")
    print("-" * 60)
    print(f"{'Total Events':<25} | {results_1k['count']:<15} | {results_10k['count']:<15}")
    print(f"{'Duration (seconds)':<25} | {results_1k['duration_seconds']:<15} | {results_10k['duration_seconds']:<15}")
    print(f"{'Throughput (events/sec)':<25} | {results_1k['throughput_eps']:<15} | {results_10k['throughput_eps']:<15}")
    print(f"{'Peak Memory Usage (MB)':<25} | {results_1k['peak_memory_mb']:<15} | {results_10k['peak_memory_mb']:<15}")
    print(f"{'Final Memory State (MB)':<25} | {results_1k['current_memory_mb']:<15} | {results_10k['current_memory_mb']:<15}")
    print("=" * 60)

if __name__ == "__main__":
    main()
