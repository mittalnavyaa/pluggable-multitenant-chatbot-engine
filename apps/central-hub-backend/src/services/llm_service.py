import logging
from typing import List, Dict, Generator

from config.settings import Settings
from llm.provider_factory import ProviderFactory

logger = logging.getLogger("llm_service")

class LLMService:
    """Service class caching the shared LLM Provider singleton instance."""

    _provider_instance = None
    _settings_instance = None

    @classmethod
    def get_provider(cls):
        """Retrieves or instantiates the LLM provider singleton."""
        if cls._provider_instance is None:
            try:
                cls._settings_instance = Settings.from_env()
                cls._provider_instance = ProviderFactory.create(cls._settings_instance)
                logger.info(f"Shared LLM Provider '{cls._provider_instance.provider_name}' initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize LLM provider: {e}")
                raise e
        return cls._provider_instance

    @classmethod
    def get_settings(cls):
        """Retrieves settings instance."""
        if cls._settings_instance is None:
            cls.get_provider()
        return cls._settings_instance

    @classmethod
    def generate(cls, messages: List[Dict[str, str]]) -> str:
        provider = cls.get_provider()
        return provider.generate(messages, temperature=cls.get_settings().temperature)

    @classmethod
    def generate_stream(cls, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        provider = cls.get_provider()
        return provider.generate_stream(messages, temperature=cls.get_settings().temperature)
