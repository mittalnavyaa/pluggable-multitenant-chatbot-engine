# apps/central-hub-backend/src/telemetry/synthetic/generator.py

import random
import uuid
import logging
import urllib.request
import urllib.error
import json
import os
from typing import List, Dict, Any, Optional, Tuple

from src.telemetry.synthetic.config import GeneratorConfig
from src.telemetry.synthetic.templates import get_dialog, ERROR_SCENARIOS, TRANSLATIONS
from src.telemetry.synthetic.metadata import MetadataGenerator
from src.telemetry.synthetic.validator import TelemetryValidator

logger = logging.getLogger("synthetic_telemetry_generator")

# Deterministic Bot UUIDs map for tenants
BOT_UUIDS = {
    "tensor": "00000000-0000-0000-0000-000000000001",
    "admissions": "00000000-0000-0000-0000-000000000002",
    "internal-support": "00000000-0000-0000-0000-000000000003",
    "hr-portal": "00000000-0000-0000-0000-000000000004",
    "placement-cell": "00000000-0000-0000-0000-000000000005",
    "website-analyzer": "00000000-0000-0000-0000-000000000006",
    "knowledge-base": "00000000-0000-0000-0000-000000000007"
}

class SyntheticTelemetryGenerator:
    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()
        
        # Initialize random state
        self.random = random.Random()
        if self.config.random_seed is not None:
            self.random.seed(self.config.random_seed)
            
        self.metadata_gen = MetadataGenerator(self.random)
        
        # Load API keys for LLM
        self.api_key = self.config.groq_api_key or os.getenv("GROQ_API_KEY")

    def generate(self) -> List[Dict[str, Any]]:
        """Generates the synthetic telemetry dataset based on config distributions."""
        dataset = []
        rejected_count = 0
        
        logger.info(f"Generating {self.config.total_conversations} synthetic telemetry records...")

        # Convert distributions to cumulative lists for sampling
        tenants, t_weights = zip(*self.config.tenant_distribution.items())
        intents, i_weights = zip(*self.config.intent_distribution.items())
        leads, l_weights = zip(*self.config.lead_distribution.items())

        for _ in range(self.config.total_conversations):
            # 1. Sample tenant and intent
            tenant = self.random.choices(tenants, weights=t_weights, k=1)[0]
            intent = self.random.choices(intents, weights=i_weights, k=1)[0]
            lead_intensity = self.random.choices(leads, weights=l_weights, k=1)[0]

            # 2. Check if this conversation represents an error event
            is_error = self.random.random() < self.config.error_rate
            
            # 3. Generate timestamps and user profiles
            timestamp = self.metadata_gen.generate_timestamp(self.config.date_range_days)
            user_profile = self.metadata_gen.generate_user_profile()
            latencies = self.metadata_gen.generate_latencies()
            
            # 4. Generate dialogue query/response
            query_text = ""
            assistant_response = ""
            error_type = None
            error_reason = None
            
            if is_error:
                error_choice = self.random.choice(ERROR_SCENARIOS)
                error_type = error_choice["status"]
                error_reason = error_choice["error_reason"]
                query_text = error_choice["payload"]["query"]
                assistant_response = error_choice["payload"]["assistant_response"]
            else:
                # Normal conversation: check if LLM should be used
                if self.config.use_llm and self.api_key:
                    query_text, assistant_response = self._generate_via_llm(tenant, intent)
                
                # Fallback to local template if LLM is disabled or failed
                if not query_text or not assistant_response:
                    dialog = get_dialog(tenant, intent, self.random)
                    # Pick first turn for single payload model
                    query_text = dialog[0][0]
                    assistant_response = dialog[0][1]

                    # Translate if user profile language is Spanish/French/Hindi
                    lang = user_profile.get("language")
                    if lang in TRANSLATIONS and self.random.random() < 0.7:
                        # Translate standard values
                        if "pricing" in query_text.lower() or "cost" in query_text.lower():
                            query_text = TRANSLATIONS[lang]["pricing"]
                        elif "hello" in query_text.lower() or "hi" in query_text.lower():
                            query_text = TRANSLATIONS[lang]["greeting"]
                        elif "error" in query_text.lower() or "issue" in query_text.lower() or "broken" in query_text.lower():
                            query_text = TRANSLATIONS[lang]["support"]

            # 5. Calculate lead score
            is_sales_lead = False
            lead_score = 0.0
            
            if not is_error:
                if lead_intensity == "High":
                    lead_score = round(self.random.uniform(0.70, 0.99), 2)
                    is_sales_lead = True
                elif lead_intensity == "Medium":
                    lead_score = round(self.random.uniform(0.30, 0.69), 2)
                    is_sales_lead = True
                else:
                    lead_score = round(self.random.uniform(0.0, 0.29), 2)
                    is_sales_lead = False

            # Normalize token counts based on length of messages
            token_count = int((len(query_text) + len(assistant_response)) / 4) + self.random.randint(10, 30)

            # 6. Build event dictionary
            event_id = str(uuid.uuid4())
            conversation_id = str(uuid.uuid4())
            bot_id = BOT_UUIDS.get(tenant, "00000000-0000-0000-0000-000000000000")

            payload = {
                "event_id": event_id,
                "conversation_id": conversation_id,
                "platform_id": tenant,
                "bot_id": bot_id,
                "timestamp": timestamp.isoformat() + "Z",
                "payload": {
                    "query": query_text,
                    "assistant_response": assistant_response,
                    "response_latency_ms": latencies["total_latency"],
                    "token_usage": token_count
                },
                "metadata": {
                    "user_region": user_profile["user_region"],
                    "browser": user_profile["browser"],
                    "device_type": user_profile["device_type"],
                    "language": user_profile["language"],
                    "is_returning_user": user_profile["is_returning_user"],
                    "worker_version": user_profile["worker_version"],
                    "vector_search_latency": latencies["vector_search_latency"],
                    "llm_latency": latencies["llm_latency"],
                    "processing_time": latencies["processing_time"],
                    "cache_hit": latencies["cache_hit"],
                    "retry_count": latencies["retry_count"]
                },
                
                # Extra metadata tracking fields for SQL exporter and validators
                "intent": intent if not is_error else "Other",
                "is_sales_lead": is_sales_lead,
                "lead_score": lead_score if not is_error else 0.0,
                "lead_priority": lead_intensity if not is_error else "Not a Lead",
                "is_error": is_error,
                "error_type": error_type,
                "error_reason": error_reason
            }

            # 7. Validate generated payload
            try:
                TelemetryValidator.validate_payload(payload)
                dataset.append(payload)
            except Exception as ve:
                logger.warning(f"Discarding invalid synthetic payload event: {ve}")
                rejected_count += 1

        logger.info(f"Synthetic generation complete: {len(dataset)} records generated, {rejected_count} rejected.")
        return dataset

    def _generate_via_llm(self, tenant: str, intent: str) -> Tuple[str, str]:
        """Queries Groq API to produce a dynamic contextual chat turn."""
        prompt = (
            f"Generate a realistic single-turn chat interaction between a user and an AI assistant. "
            f"The chatbot is configured for the tenant platform: '{tenant}' and the query business intent category is: '{intent}'. "
            f"Ensure the chatbot's tone matches the business brand. "
            f"Return ONLY a raw JSON block with 'query' and 'assistant_response' keys. Do not include markdown wraps."
        )
        
        payload = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"].strip()
            # Clean JSON wrapper
            if content.startswith("```"):
                content = content.replace("```json", "", 1).replace("```", "", 1).strip()
            parsed = json.loads(content)
            return parsed.get("query", ""), parsed.get("assistant_response", "")
        except Exception as e:
            logger.error(f"Groq API dialogue generation failed: {e}. Falling back to local templates.")
            return "", ""
