# apps/central-hub-backend/src/analytics/lead_detection/conversation_parser.py

from typing import List, Dict, Any
from src.analytics.lead_detection.schemas import ConversationMessage

class ConversationParser:
    @staticmethod
    def preprocess(messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Normalizes and extracts telemetry metadata from raw messages."""
        user_texts = []
        assistant_texts = []
        full_transcript = []

        for msg in messages:
            text_cleaned = msg.text.strip()
            if not text_cleaned:
                continue

            # Skip common automated bot greeting prefixes if present
            if text_cleaned.startswith(("[System]", "Welcome to Envoy AI!")):
                continue

            full_transcript.append(f"{msg.role}: {text_cleaned}")
            
            if msg.role == "user":
                user_texts.append(text_cleaned)
            elif msg.role == "assistant":
                assistant_texts.append(text_cleaned)

        # Basic duration proxy: message count * 1.5 minutes average duration
        duration_est_min = round(len(full_transcript) * 1.5, 1)

        return {
            "user_messages": user_texts,
            "assistant_responses": assistant_texts,
            "transcript_text": "\n".join(full_transcript),
            "message_count": len(full_transcript),
            "user_message_count": len(user_texts),
            "duration_minutes": duration_est_min
        }
