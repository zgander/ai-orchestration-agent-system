from typing import List, Dict, Any

from app.agents.base_agent import BaseAgent
from app.models.investigation_models import AgentType, InvestigationTask
from app.agents.prompts.execution_prompt import EXECUTION_SYSTEM_PROMPT, build_execution_prompt
from app.config.settings import Settings

class ExecutionFlowAgent(BaseAgent):
    def __init__(self, llm, tools: list, settings: Settings):
        super().__init__(AgentType.EXECUTION_FLOW, llm, tools, settings)

    def get_system_prompt(self) -> str:
        return EXECUTION_SYSTEM_PROMPT

    def get_task_prompt(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        return build_execution_prompt(tasks, context)
