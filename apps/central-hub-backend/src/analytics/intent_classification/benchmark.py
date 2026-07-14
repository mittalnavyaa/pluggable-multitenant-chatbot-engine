# apps/central-hub-backend/src/analytics/intent_classification/benchmark.py

import argparse
import sys
import os
import json
import time
from typing import List, Dict, Any

# Resolve path mappings
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(current_dir)
while project_root and not os.path.exists(os.path.join(project_root, "package.json")):
    parent = os.path.dirname(project_root)
    if parent == project_root:
        break
    project_root = parent

sys.path.insert(0, os.path.join(project_root, "apps", "central-hub-backend"))

# Clear potential conflicting imports
for m in list(sys.modules.keys()):
    if m == "config" or m.startswith("config."):
        pass

from src.database.database import SessionLocal
from src.analytics.intent_classification.classifier import IntentClassifierService
from src.analytics.intent_classification.evaluator import IntentEvaluator
from src.analytics.intent_classification.validator import SUPPORTED_INTENTS
from src.analytics.intent_classification.config import IntentClassificationConfig

# Standard Mock Object matching Message model
class SimpleMessageMock:
    def __init__(self, sender: str, text: str) -> None:
        self.sender = sender
        self.text = text

# The Benchmark Dataset
SYNTHETIC_DATASET = [
    {
        "true_intent": "Course Inquiry",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "Hello, do you offer a course on advanced machine learning algorithms?"),
            SimpleMessageMock("assistant", "Yes! We have an Advanced ML curriculum covering deep neural networks, transformer models, and reinforcement learning. Would you like to review the syllabus?"),
            SimpleMessageMock("user", "Yes, please. I want to see the syllabus and curriculum details.")
        ]
    },
    {
        "true_intent": "Admissions",
        "platform_id": "admissions",
        "messages": [
            SimpleMessageMock("user", "What are the eligibility requirements for the winter intake program?"),
            SimpleMessageMock("assistant", "Applicants require a Bachelor's degree in CS or STEM, transcripts, and 2 letters of recommendation. Deadlines are October 31st."),
            SimpleMessageMock("user", "Are international student transcripts accepted without translation?")
        ]
    },
    {
        "true_intent": "Pricing",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "How much does the corporate training plan cost for 15 developers?"),
            SimpleMessageMock("assistant", "Our team plans start at $199/user/month, but we offer custom pricing for larger teams. I can schedule a sales callback."),
            SimpleMessageMock("user", "Yes, what is the custom quote for 15 users?")
        ]
    },
    {
        "true_intent": "Registration",
        "platform_id": "web",
        "messages": [
            SimpleMessageMock("user", "I am trying to sign up on your portal but the registration email never arrived."),
            SimpleMessageMock("assistant", "Please check your spam or junk folder. The registration token expires in 15 minutes."),
            SimpleMessageMock("user", "I checked junk, nothing. Can you resend the registration verification token?")
        ]
    },
    {
        "true_intent": "Billing",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "My credit card was charged twice on this month's invoice. Please refund the extra $49."),
            SimpleMessageMock("assistant", "I apologize for the inconvenience. Let me retrieve your account details to initiate the refund process."),
            SimpleMessageMock("user", "The invoice number is INV-2026-987.")
        ]
    },
    {
        "true_intent": "Technical Support",
        "platform_id": "web",
        "messages": [
            SimpleMessageMock("user", "The chatbot widget keeps throwing a NullPointerException at line 142 during loading."),
            SimpleMessageMock("assistant", "That sounds like a configuration mismatch. Please check your platform integration ID."),
            SimpleMessageMock("user", "I checked the console, it says TypeError: Cannot read properties of undefined.")
        ]
    },
    {
        "true_intent": "Product Information",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "Does the backend SDK support token streaming with SSE?"),
            SimpleMessageMock("assistant", "Yes, our chatbot backend SDK supports streaming via server-sent events out of the box."),
            SimpleMessageMock("user", "Does it require Node.js or can we use Python?")
        ]
    },
    {
        "true_intent": "Documentation",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "Where can I find the installation steps for the react widget component?"),
            SimpleMessageMock("assistant", "You can check our docs portal at docs.envoy.ai/react-widget-setup."),
            SimpleMessageMock("user", "Is there a README markdown file in the Github repo?")
        ]
    },
    {
        "true_intent": "Feature Request",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "It would be amazing if the chat widget had a dark mode option natively."),
            SimpleMessageMock("assistant", "Thank you for the suggestion! I will log this for our UI engineering team."),
            SimpleMessageMock("user", "Yes, dark theme would make it much cleaner to integrate.")
        ]
    },
    {
        "true_intent": "Bug Report",
        "platform_id": "web",
        "messages": [
            SimpleMessageMock("user", "The search bar in the settings page overlaps with the delete button, making it impossible to click delete."),
            SimpleMessageMock("assistant", "Thank you for reporting this issue. We will investigate the CSS layout bug immediately."),
            SimpleMessageMock("user", "Here is a screenshot of the overlap on mobile viewports.")
        ]
    },
    {
        "true_intent": "Complaint",
        "platform_id": "web",
        "messages": [
            SimpleMessageMock("user", "This is the third time I'm trying to contact support and no one has responded! Very frustrating service."),
            SimpleMessageMock("assistant", "I am deeply sorry for the delay. Let me check the ticket queue right now to prioritize your request."),
            SimpleMessageMock("user", "I want an manager callback immediately.")
        ]
    },
    {
        "true_intent": "Feedback",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "The new layout is fantastic and the search latency is so fast now! Great work!"),
            SimpleMessageMock("assistant", "Thank you so much! We are thrilled to hear that you're liking the updates."),
            SimpleMessageMock("user", "Keep up the excellent work guys.")
        ]
    },
    {
        "true_intent": "Sales Inquiry",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "I would like to schedule a product walkthrough demo next Monday morning."),
            SimpleMessageMock("assistant", "We would love to show you a demo! I can send you a scheduling calendar link."),
            SimpleMessageMock("user", "Perfect, please send the link to bookings@enterprise.com.")
        ]
    },
    {
        "true_intent": "Enterprise Inquiry",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "We are a bank and need a completely on-premise deployment with a dedicated SLA."),
            SimpleMessageMock("assistant", "Our enterprise tier supports VPC deployments, dedicated databases, and 99.99% SLAs. Let me patch you to our enterprise sales director."),
            SimpleMessageMock("user", "Yes, we need custom compliance documentation as well.")
        ]
    },
    {
        "true_intent": "General Information",
        "platform_id": "tensor",
        "messages": [
            SimpleMessageMock("user", "Hi there, where are your corporate headquarters located?"),
            SimpleMessageMock("assistant", "Our corporate headquarters are located in San Francisco, California. We also have offices in New York and London."),
            SimpleMessageMock("user", "Great, thanks! What are your standard business hours?")
        ]
    },
    {
        "true_intent": "Other",
        "platform_id": "web",
        "messages": [
            SimpleMessageMock("user", "hello hi hey"),
            SimpleMessageMock("assistant", "Hello! How can I help you today?"),
            SimpleMessageMock("user", "just testing thanks")
        ]
    },
    {
        "true_intent": "Other",
        "platform_id": "web",
        "messages": [
            SimpleMessageMock("user", "Is the weather nice?"),
            SimpleMessageMock("assistant", "I am a support assistant and do not have access to live weather data. Is there anything else I can assist you with?"),
            SimpleMessageMock("user", "No worries.")
        ]
    }
]

class IntentClassificationBenchmark:
    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        if use_mock:
            os.environ["INTENT_LLM_PROVIDER"] = "mock"
        else:
            os.environ["INTENT_LLM_PROVIDER"] = "groq"

    def run_eval(self) -> Dict[str, Any]:
        db = SessionLocal()
        classifier = IntentClassifierService(db=db)
        
        predictions = []
        targets = []
        latencies = []
        valid_json_count = 0
        hallucination_count = 0

        total_samples = len(SYNTHETIC_DATASET)
        print(f"Running evaluation benchmark on {total_samples} synthetic conversations...")

        for idx, sample in enumerate(SYNTHETIC_DATASET):
            true_intent = sample["true_intent"]
            platform_id = sample["platform_id"]
            messages = sample["messages"]

            # Format mock conversation ID
            session_id = f"benchmark_sess_{idx}"

            # Mock data ingestion in the session:
            # Delete previous messages if they exist in DB (to avoid key collisions)
            from src.models.analytics import ChatMessageAnalytics, ChatSessionAnalytics
            db.query(ChatMessageAnalytics).filter_by(session_id=session_id).delete()
            db.query(ChatSessionAnalytics).filter_by(session_id=session_id).delete()
            db.commit()

            # Insert parent session mock in Postgres database
            db_session = ChatSessionAnalytics(
                session_id=session_id,
                platform_id=platform_id,
                message_count=len(messages),
                created_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            db.add(db_session)
            db.commit()

            # Insert message mocks in Postgres database so classifier can retrieve them
            for msg_idx, msg in enumerate(messages):
                db_msg = ChatMessageAnalytics(
                    session_id=session_id,
                    message_id=f"msg_bench_{idx}_{msg_idx}",
                    sender=msg.sender,
                    text=msg.text,
                    created_at=time.strftime('%Y-%m-%d %H:%M:%S')
                )
                db.add(db_msg)
            db.commit()

            # Execute classification
            start_time = time.time()
            try:
                res = classifier.classify_session(session_id=session_id, platform_id=platform_id)
                latency = (time.time() - start_time) * 1000.0
                
                predictions.append(res.intent)
                targets.append(true_intent)
                latencies.append(latency)

                # Check JSON parsing validity (If confidence is 0.0, fallback was triggered due to parsing/validation error)
                if res.confidence > 0.0 or res.reasoning != ["Failed to validate or parse LLM output. Triggered default fallback."]:
                    valid_json_count += 1
                
                # Check Hallucination (Returns intent NOT in canonical list)
                if res.intent not in SUPPORTED_INTENTS:
                    hallucination_count += 1

            except Exception as e:
                logger.error(f"Error classifying sample {idx}: {e}")
                predictions.append("Other")
                targets.append(true_intent)
                latencies.append(0.0)

        # Cleanup ingested mock benchmark rows
        for idx in range(total_samples):
            session_id = f"benchmark_sess_{idx}"
            db.query(ChatMessageAnalytics).filter_by(session_id=session_id).delete()
            db.query(ChatSessionAnalytics).filter_by(session_id=session_id).delete()
        db.commit()
        db.close()

        # Calculate final metrics
        metrics = IntentEvaluator.calculate_classification_metrics(predictions, targets)
        op_metrics = IntentEvaluator.calculate_operational_metrics(
            latencies=latencies,
            valid_json_count=valid_json_count,
            total=total_samples,
            hallucination_count=hallucination_count
        )

        return {"metrics": metrics, "op_metrics": op_metrics, "predictions": predictions}

    def measure_determinism(self) -> float:
        """Runs the benchmark twice and measures similarity of predictions."""
        print("Running determinism check (Trial 1)...")
        trial1 = self.run_eval()
        
        print("Running determinism check (Trial 2)...")
        trial2 = self.run_eval()

        preds1 = trial1["predictions"]
        preds2 = trial2["predictions"]

        matches = sum(1 for p1, p2 in zip(preds1, preds2) if p1 == p2)
        rate = matches / len(preds1) if preds1 else 1.0
        print(f"Determinism Consistency Rate: {rate*100:.2f}%\n")
        return rate

def main():
    parser = argparse.ArgumentParser(description="Intent Classification Telemetry Benchmark Suite")
    parser.add_argument("--mock", action="store_true", help="Force Mock LLM Provider execution (offline mode)")
    parser.add_argument("--determinism", action="store_true", help="Run determinism trial benchmarks")
    args = parser.parse_args()

    benchmark = IntentClassificationBenchmark(use_mock=args.mock)
    
    if args.determinism:
        benchmark.measure_determinism()
    else:
        results = benchmark.run_eval()
        IntentEvaluator.print_summary_report(results["metrics"], results["op_metrics"])

if __name__ == "__main__":
    main()
