import json
from datetime import datetime, timezone

from app.graph.state import InvestigationState
from app.models.investigation_models import InvestigationPlan, AgentType, TimelineEvent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.architecture_agent import ArchitectureAgent
from app.agents.execution_flow_agent import ExecutionFlowAgent
from app.agents.api_data_agent import APIDataAgent
from app.agents.setup_agent import SetupAgent
from app.tools.repository_tools import get_repository_tree, read_file, search_files, list_directory
from app.tools.analysis_tools import get_tech_stack, get_dependency_graph, get_entry_points, get_api_endpoints, get_environment_variables, search_symbols, get_file_dependencies
from app.tools.tool_context import set_root_path

class WorkflowNodes:
    def __init__(self, llm, settings):
        self.llm = llm
        self.settings = settings

    def supervisor_node(self, state: InvestigationState) -> dict:
        agent = SupervisorAgent(self.llm)
        plan = agent.create_plan(
            state["repository_name"],
            state["analysis_result_json"],
            state["user_role"],
            state["user_question"]
        )
        
        event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=AgentType.SUPERVISOR,
            event="Supervisor created investigation plan",
            detail=f"Created {len(plan.tasks)} tasks."
        )
        
        return {
            "investigation_plan": plan.model_dump_json(),
            "timeline_events": [event.model_dump_json()],
            "current_stage": "investigate"
        }

    def _run_specialist(self, agent_class, agent_type: AgentType, tools: list, state: InvestigationState) -> dict:
        # Bind the root path for tools
        set_root_path(state["repository_path"])
        
        plan_dict = json.loads(state.get("investigation_plan", "{}"))
        plan = InvestigationPlan(**plan_dict) if plan_dict else None
        
        tasks = [t for t in plan.tasks if t.agent_type == agent_type] if plan else []
        if not tasks:
            return {}
            
        agent = agent_class(self.llm, tools, self.settings)
        context = {
            "repository_name": state["repository_name"],
            "repository_path": state["repository_path"]
        }
        
        report = agent.run(tasks, context)
        
        event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=agent_type,
            event=f"{agent_type.value} completed investigation",
            detail=f"Found {len(report.findings)} findings." if report.findings else f"Failed: {report.error}"
        )
        
        report_key = f"{agent_type.value.lower()}_report"
        return {
            report_key: report.model_dump_json(),
            "timeline_events": [event.model_dump_json()]
        }

    def architecture_node(self, state: InvestigationState) -> dict:
        tools = [get_repository_tree, get_tech_stack, get_dependency_graph, get_entry_points, read_file, list_directory]
        return self._run_specialist(ArchitectureAgent, AgentType.ARCHITECTURE, tools, state)

    def execution_flow_node(self, state: InvestigationState) -> dict:
        tools = [get_entry_points, get_dependency_graph, search_symbols, read_file, get_file_dependencies]
        return self._run_specialist(ExecutionFlowAgent, AgentType.EXECUTION_FLOW, tools, state)

    def api_data_node(self, state: InvestigationState) -> dict:
        tools = [get_api_endpoints, get_dependency_graph, get_repository_tree, search_symbols, read_file]
        return self._run_specialist(APIDataAgent, AgentType.API_DATA, tools, state)

    def setup_node(self, state: InvestigationState) -> dict:
        tools = [get_tech_stack, get_environment_variables, read_file, search_files, get_repository_tree]
        return self._run_specialist(SetupAgent, AgentType.SETUP, tools, state)
        
    def merge_results_node(self, state: InvestigationState) -> dict:
        event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=AgentType.SUPERVISOR,
            event="Investigation completed"
        )
        return {
            "current_stage": "done",
            "timeline_events": [event.model_dump_json()]
        }
