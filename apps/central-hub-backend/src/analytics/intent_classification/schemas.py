# apps/central-hub-backend/src/analytics/intent_classification/schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NormalizedMessage(BaseModel):
    sender: str = Field(..., description="Role of the sender: 'user' or 'bot' / 'assistant'")
    text: str = Field(..., description="The cleaned message content")

class NormalizedConversation(BaseModel):
    session_id: str = Field(..., description="Chat session identifier")
    platform_id: str = Field(..., description="Platform or tenant client identifier")
    messages: List[NormalizedMessage] = Field(..., description="Chronological cleaned conversation transcript")
    duration_minutes: float = Field(..., description="Estimated or tracked conversation duration in minutes")
    message_count: int = Field(..., description="Total message count in the conversation")

class IntentClassificationResult(BaseModel):
    intent: str = Field(..., description="Primary classified business intent")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    secondary_intents: List[str] = Field(default_factory=list, description="Other secondary intents observed")
    reasoning: List[str] = Field(..., description="Concise explainable factors for the chosen primary intent")

class ClassificationMetrics(BaseModel):
    processing_time_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retry_attempts: int = 0
    parsing_error: Optional[str] = None
    fallback_triggered: bool = False
