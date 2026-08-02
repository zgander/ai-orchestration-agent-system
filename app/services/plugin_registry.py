from typing import Dict, Any, Callable, List
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PluginRegistry:
    _instance = None
    
    def __init__(self):
        self.analyzers: Dict[str, Callable] = {}
        self.specialist_agents: Dict[str, Callable] = {}
        self.reviewers: Dict[str, Callable] = {}
        self.exporters: Dict[str, Callable] = {}
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_analyzer(self, name: str, func: Callable):
        self.analyzers[name] = func
        logger.info(f"Registered plugin analyzer: {name}")

    def register_specialist_agent(self, name: str, func: Callable):
        self.specialist_agents[name] = func
        logger.info(f"Registered plugin specialist agent: {name}")
        
    def register_reviewer(self, name: str, func: Callable):
        self.reviewers[name] = func
        logger.info(f"Registered plugin reviewer: {name}")
        
    def register_exporter(self, name: str, func: Callable):
        self.exporters[name] = func
        logger.info(f"Registered plugin exporter: {name}")

    def get_analyzers(self) -> Dict[str, Callable]:
        return self.analyzers
        
    def get_specialist_agents(self) -> Dict[str, Callable]:
        return self.specialist_agents
        
    def get_reviewers(self) -> Dict[str, Callable]:
        return self.reviewers
        
    def get_exporters(self) -> Dict[str, Callable]:
        return self.exporters

# Decorators for easy registration
def register_analyzer(name: str):
    def decorator(func):
        PluginRegistry.get_instance().register_analyzer(name, func)
        return func
    return decorator

def register_specialist_agent(name: str):
    def decorator(func):
        PluginRegistry.get_instance().register_specialist_agent(name, func)
        return func
    return decorator
