from typing import List, Dict, Any

from app.agents.base_agent import BaseAgent
from app.models.investigation_models import AgentType, InvestigationTask
from app.agents.prompts.setup_prompt import SETUP_SYSTEM_PROMPT, build_setup_prompt
from app.config.settings import Settings

class SetupAgent(BaseAgent):
    def __init__(self, llm, tools: list, settings: Settings):
        super().__init__(AgentType.SETUP, llm, tools, settings)

    def get_system_prompt(self) -> str:
        return SETUP_SYSTEM_PROMPT

    def get_task_prompt(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        return build_setup_prompt(tasks, context)
