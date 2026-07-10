"""Layer 2: Tenant Profile Identity Injection."""

from src.rag.prompts.prompt_models import TenantProfile

def get_tenant_profile_prefix(profile: TenantProfile) -> str:
    """
    Constructs the tenant profile layer based on authenticated platform details.
    Allows the same LLM deployment to adapt its tone and identity dynamically per tenant.
    """
    tenant_details = (
        "==============================\n"
        "TENANT PROFILE\n"
        "==============================\n"
        f"Company Name: {profile.company_name}\n"
        f"Product Name: {profile.product_name}\n"
        f"Bot Display Name: {profile.bot_name}\n"
        f"Preferred Communication Tone: {profile.brand_tone}\n"
    )
    
    if profile.support_url:
        tenant_details += f"Support Web Portal: {profile.support_url}\n"
    if profile.contact_email:
        tenant_details += f"Contact Email: {profile.contact_email}\n"
    if profile.allowed_terminology:
        terms_str = ", ".join(profile.allowed_terminology)
        tenant_details += f"Brand Terminology & Glossary: {terms_str}\n"

    return tenant_details
