"""Configuration settings for the payload stamping layer."""

import os
from dataclasses import dataclass

@dataclass
class StampingConfig:
    """Configurable options for multi-tenant verification and schema checks."""
    tenant_field_name: str = "platform_id"
    schema_version: str = "1.1.0"
    enable_security_alert: bool = True

    @classmethod
    def from_env(cls) -> "StampingConfig":
        return cls(
            tenant_field_name=os.getenv("TENANT_FIELD_NAME", "platform_id").strip(),
            schema_version=os.getenv("STAMPING_SCHEMA_VERSION", "1.1.0").strip(),
            enable_security_alert=os.getenv("ENABLE_SECURITY_ALERT", "True").strip().lower() == "true"
        )
