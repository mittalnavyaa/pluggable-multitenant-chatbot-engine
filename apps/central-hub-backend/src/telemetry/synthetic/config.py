# apps/central-hub-backend/src/telemetry/synthetic/config.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class GeneratorConfig(BaseModel):
    total_conversations: int = Field(default=1000, description="Total number of conversations to generate")
    random_seed: Optional[int] = Field(default=42, description="Random seed for deterministic generation")
    
    tenant_distribution: Dict[str, float] = Field(
        default_factory=lambda: {
            "tensor": 0.15,
            "admissions": 0.20,
            "internal-support": 0.15,
            "hr-portal": 0.15,
            "placement-cell": 0.10,
            "website-analyzer": 0.10,
            "knowledge-base": 0.15
        },
        description="Scoping probabilities across internal tenant platforms (sum must equal 1.0)"
    )
    
    intent_distribution: Dict[str, float] = Field(
        default_factory=lambda: {
            "Course Inquiry": 0.10,
            "Admissions": 0.12,
            "Pricing": 0.08,
            "Registration": 0.05,
            "Billing": 0.05,
            "Technical Support": 0.10,
            "Product Information": 0.10,
            "Documentation": 0.08,
            "Feature Request": 0.04,
            "Bug Report": 0.04,
            "Complaint": 0.04,
            "Feedback": 0.04,
            "Sales Inquiry": 0.06,
            "Enterprise Inquiry": 0.04,
            "General Information": 0.08,
            "Other": 0.02
        },
        description="Canonical intent categories mapping probabilities (sum must equal 1.0)"
    )
    
    lead_distribution: Dict[str, float] = Field(
        default_factory=lambda: {
            "Low": 0.65,
            "Medium": 0.20,
            "High": 0.15
        },
        description="Distribution of sales lead priority intensity"
    )
    
    date_range_days: int = Field(default=30, description="Time span window backward from now in days")
    error_rate: float = Field(default=0.05, description="Percentage of sessions containing errors / failures")
    languages: List[str] = Field(default_factory=lambda: ["en", "es", "fr", "hi"], description="List of supported languages")
    
    use_llm: bool = Field(default=False, description="Whether to call actual LLM API (Groq) for generation")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API token. Overrides environment settings.")
