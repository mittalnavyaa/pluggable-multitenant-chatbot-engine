# apps/central-hub-backend/src/analytics/intent_classification/evaluator.py

import time
import logging
from typing import List, Dict, Any
from collections import defaultdict
from src.analytics.intent_classification.validator import SUPPORTED_INTENTS

logger = logging.getLogger("intent_evaluator")

class IntentEvaluator:
    @staticmethod
    def calculate_classification_metrics(
        predictions: List[str],
        targets: List[str]
    ) -> Dict[str, Any]:
        """Computes Precision, Recall, F1-Score, and Accuracy."""
        total = len(targets)
        if total == 0:
            return {"accuracy": 0.0, "macro_f1": 0.0, "classes": {}}

        correct = sum(1 for p, t in zip(predictions, targets) if p.strip().lower() == t.strip().lower())
        accuracy = correct / total

        # Per-class counts
        tp = defaultdict(int)
        fp = defaultdict(int)
        fn = defaultdict(int)
        support = defaultdict(int)

        all_classes = set(targets) | set(predictions)

        for p, t in zip(predictions, targets):
            p_clean = p.strip()
            t_clean = t.strip()
            support[t_clean] += 1
            if p_clean.lower() == t_clean.lower():
                tp[t_clean] += 1
            else:
                fp[p_clean] += 1
                fn[t_clean] += 1

        class_metrics = {}
        total_f1 = 0.0
        classes_with_support = 0

        for cls in all_classes:
            cls_tp = tp[cls]
            cls_fp = fp[cls]
            cls_fn = fn[cls]
            cls_sup = support[cls]

            precision = cls_tp / (cls_tp + cls_fp) if (cls_tp + cls_fp) > 0 else 0.0
            recall = cls_tp / (cls_tp + cls_fn) if (cls_tp + cls_fn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            class_metrics[cls] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": cls_sup
            }

            if cls_sup > 0:
                total_f1 += f1
                classes_with_support += 1

        macro_f1 = total_f1 / classes_with_support if classes_with_support > 0 else 0.0

        return {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "classes": class_metrics
        }

    @staticmethod
    def calculate_operational_metrics(
        latencies: List[float],
        valid_json_count: int,
        total: int,
        hallucination_count: int
    ) -> Dict[str, Any]:
        """Calculates latency distribution and JSON parsing / hallucination statistics."""
        if total == 0:
            return {
                "json_validity_rate": 0.0,
                "hallucination_rate": 0.0,
                "latency": {"mean": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
            }

        latencies_sorted = sorted(latencies)
        mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_idx = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_idx] if latencies_sorted else 0.0
        min_latency = latencies_sorted[0] if latencies_sorted else 0.0
        max_latency = latencies_sorted[-1] if latencies_sorted else 0.0

        return {
            "json_validity_rate": valid_json_count / total,
            "hallucination_rate": hallucination_count / total,
            "latency": {
                "mean": mean_latency,
                "p95": p95_latency,
                "min": min_latency,
                "max": max_latency
            }
        }

    @classmethod
    def print_summary_report(cls, metrics: Dict[str, Any], op_metrics: Dict[str, Any]) -> None:
        """Outputs a cleanly formatted console text summary report."""
        print("\n=======================================================")
        print(" INTENT CLASSIFICATION BENCHMARK EVALUATION SUMMARY")
        print("=======================================================")
        print(f"Accuracy:           {metrics['accuracy']*100:.2f}%")
        print(f"Macro F1 Score:     {metrics['macro_f1']*100:.2f}%")
        print(f"JSON Validity Rate: {op_metrics['json_validity_rate']*100:.2f}%")
        print(f"Hallucination Rate: {op_metrics['hallucination_rate']*100:.2f}%")
        print("\nLATENCY STATISTICS:")
        print(f"  Mean: {op_metrics['latency']['mean']:.2f}ms")
        print(f"  P95:  {op_metrics['latency']['p95']:.2f}ms")
        print(f"  Min:  {op_metrics['latency']['min']:.2f}ms")
        print(f"  Max:  {op_metrics['latency']['max']:.2f}ms")
        print("\nPER-CLASS METRICS:")
        print(f"  {'Class':<22} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
        print("  " + "-"*62)
        for cls, vals in sorted(metrics["classes"].items()):
            # Only print classes that have support
            if vals["support"] > 0:
                print(f"  {cls:<22} | {vals['precision']*100:>8.2f}% | {vals['recall']*100:>8.2f}% | {vals['f1']*100:>8.2f}% | {vals['support']:<8}")
        print("=======================================================\n")
