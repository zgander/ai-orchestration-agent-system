from typing import List, Dict, Any

from app.agents.base_agent import BaseAgent
from app.models.investigation_models import AgentType
from app.agents.prompts.api_prompt import API_SYSTEM_PROMPT, build_api_prompt
from app.config.settings import Settings

class APIDataAgent(BaseAgent):
    def __init__(self, llm, tools: list, settings: Settings):
        super().__init__(AgentType.API_DATA, llm, tools, settings)

    def get_system_prompt(self) -> str:
        return API_SYSTEM_PROMPT

    def get_task_prompt(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        return build_api_prompt(tasks, context)
