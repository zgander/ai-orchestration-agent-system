import json
import uuid
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

from app.models.investigation_models import InvestigationPlan, InvestigationTask, AgentType, AgentStatus
from app.agents.prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT, build_supervisor_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SupervisorAgent:
    def __init__(self, llm):
        self.llm = llm

    def create_plan(self, repository_name: str, analysis_result_json: str, user_role: str, user_question: str) -> InvestigationPlan:
        logger.info(f"Supervisor generating plan for {repository_name}...")
        
        system_prompt = SUPERVISOR_SYSTEM_PROMPT
        user_prompt = build_supervisor_prompt(analysis_result_json, user_role, user_question)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        content = response.content
        logger.debug(f"[SUPERVISOR] RAW LLM OUTPUT:\n{content}")
        
        from app.utils.json_parser import extract_json_from_llm
        sanitized_output = extract_json_from_llm(content, expected_type='dict')
        logger.debug(f"[SUPERVISOR] SANITIZED OUTPUT:\n{sanitized_output}")
                
        try:
            if not sanitized_output:
                raise ValueError("Sanitized JSON string is empty.")
            data = json.loads(sanitized_output)
            
            tasks = []
            for t in data.get("tasks", []):
                agent_type_str = t.get("agent_type", "")
                try:
                    clean_str = str(agent_type_str).strip().upper().replace(" ", "_")
                    if "ARCHITECTURE" in clean_str or "ARCH" in clean_str:
                        agent_type = AgentType.ARCHITECTURE
                    elif "EXEC" in clean_str or "FLOW" in clean_str:
                        agent_type = AgentType.EXECUTION_FLOW
                    elif "API" in clean_str or "DATA" in clean_str:
                        agent_type = AgentType.API_DATA
                    elif "SETUP" in clean_str:
                        agent_type = AgentType.SETUP
                    else:
                        agent_type = AgentType(clean_str)
                except ValueError:
                    logger.warning(f"Supervisor returned unknown agent type: {agent_type_str}. Defaulting to ARCHITECTURE.")
                    agent_type = AgentType.ARCHITECTURE
                    
                tasks.append(InvestigationTask(
                    task_id=t.get("task_id", str(uuid.uuid4())),
                    agent_type=agent_type,
                    description=t.get("description", ""),
                    status=AgentStatus.IDLE,
                    created_at=datetime.now(timezone.utc)
                ))
                
            return InvestigationPlan(
                repository_name=repository_name,
                tasks=tasks,
                strategy=data.get("strategy", "Standard Investigation"),
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Supervisor failed to parse JSON: {e}")
            logger.error(f"Supervisor output: {content}")
            
            # Fallback
            fallback_tasks = []
            for atype in [AgentType.ARCHITECTURE, AgentType.EXECUTION_FLOW, AgentType.API_DATA, AgentType.SETUP]:
                fallback_tasks.append(InvestigationTask(
                    task_id=str(uuid.uuid4()),
                    agent_type=atype,
                    description=f"Investigate {atype.value} aspects of the repository.",
                    status=AgentStatus.IDLE,
                    created_at=datetime.now(timezone.utc)
                ))
            return InvestigationPlan(
                repository_name=repository_name,
                tasks=fallback_tasks,
                strategy="Fallback Investigation (JSON Parsing Failed)",
                created_at=datetime.now(timezone.utc)
            )
