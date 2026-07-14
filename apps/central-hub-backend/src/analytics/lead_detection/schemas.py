# apps/central-hub-backend/src/analytics/lead_detection/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

class ConversationMessage(BaseModel):
    role: str = Field(..., description="Role of sender: user or assistant")
    text: str = Field(..., description="Message text content")

class ConversationContext(BaseModel):
    conversation_id: str
    platform_id: str
    tenant_id: str
    messages: List[ConversationMessage]

class LeadResult(BaseModel):
    conversation_id: str
    platform_id: str
    tenant_id: str
    is_lead: bool
    lead_score: float
    confidence: float
    priority: str
    intent: str
    buying_signals: List[str]
    reason: List[str]
