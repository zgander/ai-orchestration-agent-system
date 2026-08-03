from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
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

class GoogleProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def get_llm(self) -> BaseChatModel:
        logger.info(f"Initializing Google Provider with model {self.settings.google_model}")
        kwargs = {
            "model": self.settings.google_model,
            "temperature": self.settings.temperature,
            "max_output_tokens": self.settings.max_tokens,
        }
        if self.settings.google_api_key:
            kwargs["google_api_key"] = self.settings.google_api_key
            
        return ChatGoogleGenerativeAI(**kwargs)

class LLMFactory:
    @staticmethod
    def get_provider(settings: Settings) -> LLMProvider:
        provider_name = settings.llm_provider.lower()
        if provider_name == "ollama":
            return OllamaProvider(settings)
        elif provider_name == "google":
            return GoogleProvider(settings)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
            
    @staticmethod
    def get_llm(settings: Settings) -> BaseChatModel:
        provider = LLMFactory.get_provider(settings)
        return provider.get_llm()
