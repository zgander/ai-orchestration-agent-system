import json
import uuid
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from app.models.investigation_models import InvestigationPlan, InvestigationTask, AgentType, AgentStatus, SupervisorPlanOutput
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
        
        try:
            logger.info(f"Extracting structured JSON for Supervisor plan...")
            structured_llm = self.llm.with_structured_output(SupervisorPlanOutput)
            extraction_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
                ("human", "{text}")
            ])
            extractor = extraction_prompt | structured_llm
            
            data = extractor.invoke({"text": user_prompt})
            
            # Normalize common LLM agent_type variations to exact enum values
            AGENT_TYPE_ALIASES = {
                "ARCHITECTURE": AgentType.ARCHITECTURE,
                "ARCH": AgentType.ARCHITECTURE,
                "EXECUTION_FLOW": AgentType.EXECUTION_FLOW,
                "EXECUTION": AgentType.EXECUTION_FLOW,
                "EXEC": AgentType.EXECUTION_FLOW,
                "API_DATA": AgentType.API_DATA,
                "API": AgentType.API_DATA,
                "API_AND_DATA": AgentType.API_DATA,
                "DATA": AgentType.API_DATA,
                "SETUP": AgentType.SETUP,
                "SETUP_ENVIRONMENT": AgentType.SETUP,
                "SETUP_ENV": AgentType.SETUP,
                "ENVIRONMENT": AgentType.SETUP,
            }
            
            tasks = []
            if data and data.tasks:
                for t in data.tasks:
                    normalized_key = t.agent_type.strip().upper().replace(" ", "_").replace("&", "AND")
                    agent_type = AGENT_TYPE_ALIASES.get(normalized_key)
                    if not agent_type:
                        logger.warning(f"Supervisor returned unknown agent type: '{t.agent_type}' (normalized: '{normalized_key}'). Skipping task.")
                        continue
                        
                    tasks.append(InvestigationTask(
                        task_id=t.task_id if t.task_id else str(uuid.uuid4()),
                        agent_type=agent_type,
                        description=t.description,
                        status=AgentStatus.IDLE,
                        created_at=datetime.now(timezone.utc)
                    ))
            
            # Guarantee every agent type gets at least one task
            assigned_types = {t.agent_type for t in tasks}
            for atype in [AgentType.ARCHITECTURE, AgentType.EXECUTION_FLOW, AgentType.API_DATA, AgentType.SETUP]:
                if atype not in assigned_types:
                    logger.info(f"Supervisor did not assign tasks for {atype.value}. Adding default task.")
                    tasks.append(InvestigationTask(
                        task_id=str(uuid.uuid4()),
                        agent_type=atype,
                        description=f"Investigate all {atype.value} aspects of the repository.",
                        status=AgentStatus.IDLE,
                        created_at=datetime.now(timezone.utc)
                    ))
                
            return InvestigationPlan(
                repository_name=repository_name,
                tasks=tasks,
                strategy=data.strategy if data else "Standard Investigation",
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Supervisor failed to parse structured output: {e}")
            
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
