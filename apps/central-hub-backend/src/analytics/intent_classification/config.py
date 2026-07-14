# apps/central-hub-backend/src/analytics/intent_classification/config.py

import os
from pathlib import Path

class IntentClassificationConfig:
    # LLM Settings
    PROVIDER = os.getenv("INTENT_LLM_PROVIDER", "groq").strip().lower()
    MODEL_NAME = os.getenv("INTENT_LLM_MODEL", "llama-3.3-70b-versatile").strip()
    TEMPERATURE = float(os.getenv("INTENT_LLM_TEMPERATURE", "0.0"))
    MAX_TOKENS = int(os.getenv("INTENT_LLM_MAX_TOKENS", "512"))
    TIMEOUT = float(os.getenv("INTENT_LLM_TIMEOUT", "30.0"))
    
    # Validation & Routing Settings
    CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.60"))
    PROMPT_VERSION = os.getenv("INTENT_PROMPT_VERSION", "v1.0.0").strip()

    # Paths
    BASE_DIR = Path(__file__).resolve().parent
    DEFAULT_DATASET_PATH = str(BASE_DIR / "evaluation_dataset.json")
    TAXONOMY_PATH = str(BASE_DIR / "prompts" / "taxonomy.md")
    SYSTEM_PROMPT_PATH = str(BASE_DIR / "prompts" / "system_prompt.md")
