from pydantic import BaseModel, Field
from typing import Optional, List

class TenantProfile(BaseModel):
    """Pydantic model representing tenant branding details parsed from DB ui_theme_config."""
    company_name: str = Field(default="Envoy AI Client")
    product_name: str = Field(default="Envoy Chat Service")
    bot_name: str = Field(default="Envoy Assistant")
    support_url: str = Field(default="")
    contact_email: str = Field(default="")
    brand_tone: str = Field(default="professional and precise")
    allowed_terminology: Optional[List[str]] = Field(default=None)
    fallback_message: Optional[str] = Field(default=None)
