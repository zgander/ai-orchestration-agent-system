from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def get_llm(self) -> BaseChatModel:
        logger.info(f"Initializing Ollama Provider with model {self.settings.ollama_model} at {self.settings.ollama_base_url}")
        return ChatOllama(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_model,
            temperature=self.settings.temperature,
            num_predict=self.settings.max_tokens,
        )

class LLMFactory:
    @staticmethod
    def get_provider(settings: Settings) -> LLMProvider:
        provider_name = settings.llm_provider.lower()
        if provider_name == "ollama":
            return OllamaProvider(settings)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
            
    @staticmethod
    def get_llm(settings: Settings) -> BaseChatModel:
        provider = LLMFactory.get_provider(settings)
        return provider.get_llm()
