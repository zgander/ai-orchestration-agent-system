from typing import List, Dict, Any

from app.agents.base_agent import BaseAgent
from app.models.investigation_models import AgentType, InvestigationTask
from app.agents.prompts.architecture_prompt import ARCHITECTURE_SYSTEM_PROMPT, build_architecture_prompt
from app.config.settings import Settings

class ArchitectureAgent(BaseAgent):
    def __init__(self, llm, tools: list, settings: Settings):
        super().__init__(AgentType.ARCHITECTURE, llm, tools, settings)

    def get_system_prompt(self) -> str:
        return ARCHITECTURE_SYSTEM_PROMPT

    def get_task_prompt(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        return build_architecture_prompt(tasks, context)
