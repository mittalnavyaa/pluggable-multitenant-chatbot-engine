import os
from pydantic_settings import BaseSettings

class PromptConfig(BaseSettings):
    """Configuration constraints for prompt assembly operations."""
    max_history_turns: int = int(os.getenv("PROMPT_MAX_HISTORY_TURNS", "3"))
    default_fallback_message: str = os.getenv(
        "PROMPT_DEFAULT_FALLBACK_MESSAGE",
        "I couldn't find that information in the current knowledge base. Please contact our support team for further assistance."
    )
    max_prompt_size: int = int(os.getenv("PROMPT_MAX_SIZE_CHARACTERS", "8000"))
    formatting_rules: str = os.getenv(
        "PROMPT_FORMATTING_RULES",
        "Respond in clean Markdown structure. Answer immediately without conversational greetings, introductions, or apologies."
    )
    response_tone: str = os.getenv("PROMPT_RESPONSE_TONE", "precise, helpful, and professional")
    encoding_name: str = os.getenv("PROMPT_TOKEN_ENCODING", "cl100k_base")
    prompt_version: str = os.getenv("PROMPT_VERSION", "v1.0.0")
    system_version: str = os.getenv("SYSTEM_VERSION", "v1.0.0")

    class Config:
        env_prefix = "PROMPT_"
