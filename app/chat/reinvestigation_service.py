import uuid
from datetime import datetime, timezone
from app.models.investigation_models import InvestigationTask, AgentType, AgentReport, AgentStatus
from app.models.chat_models import QueryClassification, QueryCategory
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ReInvestigationService:
    def __init__(self, llm, settings):
        self.llm = llm
        self.settings = settings

    def run(self, repository_path: str, query: str, classification: QueryClassification, analysis_result_json: str) -> AgentReport:
        logger.info(f"Running targeted reinvestigation for query: '{query}'")
        
        # Determine best agent based on category
        agent_type = AgentType.ARCHITECTURE # default
        if classification:
            if classification.category == QueryCategory.EXECUTION_FLOW:
                agent_type = AgentType.EXECUTION_FLOW
            elif classification.category == QueryCategory.API:
                agent_type = AgentType.API_DATA
            elif classification.category == QueryCategory.SETUP:
                agent_type = AgentType.SETUP
                
        # We need to instantiate the correct agent class based on agent_type
        agent = self._get_agent(agent_type, repository_path)
        
        task = InvestigationTask(
            task_id=str(uuid.uuid4()),
            agent_type=agent_type,
            description=f"Investigate the following user query and find evidence to answer it: {query}",
            created_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"Dispatching task to {agent_type.value} agent")
        try:
            from app.agents.prompts.prompt_utils import build_condensed_context
            context = {
                "repository_name": "",
                "repository_path": repository_path,
                "analysis_result_json": build_condensed_context(analysis_result_json, agent_type),
                "investigation_strategy": "Targeted reinvestigation"
            }
            report = agent.run([task], context)
            logger.info("Reinvestigation complete")
            return report
        except Exception as e:
            logger.error(f"Reinvestigation agent failed: {e}")
            # Return empty report
            return AgentReport(
                agent_type=agent_type,
                status=AgentStatus.FAILED,
                tasks=[],
                findings=[],
                tool_calls=[],
                reasoning_steps=[],
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error=str(e)
            )

    def _get_agent(self, agent_type: AgentType, repository_path: str):
        # Local import to avoid circular dependencies
        from app.agents.architecture_agent import ArchitectureAgent
        from app.agents.execution_flow_agent import ExecutionFlowAgent
        from app.agents.api_data_agent import APIDataAgent
        from app.agents.setup_agent import SetupAgent
        from app.tools.repository_tools import get_repository_tree, read_file, search_files, list_directory
        from app.tools.analysis_tools import (get_tech_stack, get_dependency_graph, get_entry_points,
            get_api_endpoints, get_environment_variables, search_symbols, get_file_dependencies)
        from app.tools.tool_context import set_root_path
        set_root_path(repository_path)
        
        if agent_type == AgentType.ARCHITECTURE:
            return ArchitectureAgent(self.llm, [get_repository_tree, read_file, list_directory, get_tech_stack, get_dependency_graph, get_entry_points], self.settings)
        elif agent_type == AgentType.EXECUTION_FLOW:
            return ExecutionFlowAgent(self.llm, [get_repository_tree, read_file, search_files, get_tech_stack, get_dependency_graph, get_entry_points], self.settings)
        elif agent_type == AgentType.API_DATA:
            return APIDataAgent(self.llm, [get_repository_tree, read_file, search_files, get_api_endpoints, search_symbols, get_file_dependencies], self.settings)
        elif agent_type == AgentType.SETUP:
            return SetupAgent(self.llm, [get_repository_tree, read_file, list_directory, search_files, get_environment_variables, get_tech_stack], self.settings)
        else:
            return ArchitectureAgent(self.llm, [get_repository_tree, read_file, list_directory, get_tech_stack, get_dependency_graph, get_entry_points], self.settings)
