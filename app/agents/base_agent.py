import json
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
import traceback
import re

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from app.models.investigation_models import (
    AgentType, AgentStatus, InvestigationTask, AgentFinding, AgentReport, ToolResult
)
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_type: AgentType, llm, tools: list, settings: Settings):
        self.agent_type = agent_type
        self.llm = llm
        self.tools = tools
        self.settings = settings

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def get_task_prompt(self, tasks: List[InvestigationTask], context: Dict[str, Any]) -> str:
        pass

    def run(self, tasks: List[InvestigationTask], context: Dict[str, Any]) -> AgentReport:
        started_at = datetime.now(timezone.utc)
        tool_calls_record = []
        reasoning_steps = []
        findings = []
        status = AgentStatus.RUNNING
        error_msg = None

        logger.info(f"{self.agent_type.value} started with {len(tasks)} tasks.")

        try:
            # We use tool-calling agent, it's more reliable than pure text ReAct
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                verbose=True, 
                max_iterations=self.settings.agent_max_iterations,
                return_intermediate_steps=True
            )

            # Pass dictionaries for context
            task_dicts = [{"description": t.description} for t in tasks]
            task_input = self.get_task_prompt(task_dicts, context)
            
            # Execute
            result = agent_executor.invoke({"input": task_input})
            
            final_output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            for action, observation in intermediate_steps:
                tool_calls_record.append(ToolResult(
                    tool_name=action.tool,
                    input_args=action.tool_input if isinstance(action.tool_input, dict) else {"input": str(action.tool_input)},
                    output=str(observation)[:500] + ("..." if len(str(observation)) > 500 else ""),
                    success=True,
                    duration_seconds=0.0
                ))
                reasoning_steps.append(f"Used tool {action.tool}")

            if "Agent stopped due to max iterations" in final_output:
                error_msg = f"Agent stopped due to max iterations ({self.settings.agent_max_iterations}). The LLM model may be stuck in a loop."
                logger.error(f"{self.agent_type.value} failed: {error_msg}")
                status = AgentStatus.FAILED
                parsed_findings = []
            else:
                # Log the exact raw output before any modifications
                logger.debug(f"[{self.agent_type.value}] RAW LLM OUTPUT:\n{final_output}")

                from app.utils.json_parser import extract_json_from_llm
                sanitized_output = extract_json_from_llm(final_output, expected_type='list')
                logger.debug(f"[{self.agent_type.value}] SANITIZED OUTPUT:\n{sanitized_output}")
                        
                try:
                    if not sanitized_output:
                        raise ValueError("Sanitized JSON string is empty.")
                    parsed_findings = json.loads(sanitized_output)
                    for f in parsed_findings:
                        findings.append(AgentFinding(**f))
                    status = AgentStatus.COMPLETED
                except Exception as e:
                    logger.error(f"Failed to parse JSON output from {self.agent_type.value}. Error: {e}\nRaw Output: {final_output}\nSanitized: {sanitized_output}")
                    error_msg = f"Failed to parse findings JSON: {e}"
                    status = AgentStatus.FAILED
            
            # Mark tasks completed
            completed_tasks = []
            for task in tasks:
                completed_tasks.append(InvestigationTask(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    description=task.description,
                    status=status,
                    created_at=task.created_at,
                    completed_at=datetime.now(timezone.utc)
                ))
            tasks = completed_tasks

        except Exception as e:
            err_str = str(e).lower()
            if "connection" in err_str or "unreachable" in err_str or "failed to connect" in err_str:
                error_msg = f"Network Error: Unable to reach Ollama Cloud endpoint at {self.settings.ollama_base_url}. Details: {str(e)}"
            elif "timeout" in err_str:
                error_msg = f"Timeout Error: Ollama Cloud response took too long. Details: {str(e)}"
            elif "404" in err_str or "not found" in err_str:
                error_msg = f"Model or Endpoint Unavailable: Please check your Ollama Cloud endpoint and verify that the model '{self.settings.ollama_model}' is supported. Details: {str(e)}"
            else:
                error_msg = f"Agent Execution Error: {str(e)}"
            
            logger.error(f"{self.agent_type.value} failed: {error_msg}")
            logger.error(traceback.format_exc())
            status = AgentStatus.FAILED

        return AgentReport(
            agent_type=self.agent_type,
            status=status,
            tasks=tasks,
            findings=findings,
            tool_calls=tool_calls_record,
            reasoning_steps=reasoning_steps,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            error=error_msg
        )
