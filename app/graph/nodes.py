import json
from datetime import datetime, timezone

from app.graph.state import InvestigationState
from app.models.investigation_models import InvestigationPlan, AgentType, AgentStatus, AgentReport, TimelineEvent
from app.models.review_models import ReviewReport, ReviewVerdict, RevisionRequest
from app.models.onboarding_models import OnboardingRole
from app.models.analysis_models import AnalysisResult
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.architecture_agent import ArchitectureAgent
from app.agents.execution_flow_agent import ExecutionFlowAgent
from app.agents.api_data_agent import APIDataAgent
from app.agents.setup_agent import SetupAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.synthesizer_agent import SynthesizerAgent
from app.tools.repository_tools import get_repository_tree, read_file, search_files, list_directory
from app.tools.analysis_tools import get_tech_stack, get_dependency_graph, get_entry_points, get_api_endpoints, get_environment_variables, search_symbols, get_file_dependencies
from app.tools.tool_context import set_root_path
from app.utils.logger import get_logger

logger = get_logger(__name__)

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
            logger.info(f"{agent_type.value} has no assigned tasks. Skipping.")
            event = TimelineEvent(
                timestamp=datetime.now(timezone.utc),
                agent_type=agent_type,
                event=f"{agent_type.value} skipped (no tasks assigned)"
            )
            report = AgentReport(
                agent_type=agent_type,
                status=AgentStatus.COMPLETED,
                tasks=[],
                findings=[],
                tool_calls=[],
                reasoning_steps=[],
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error=None
            )
            report_key = f"{agent_type.value.lower()}_report"
            return {
                report_key: report.model_dump_json(),
                "timeline_events": [event.model_dump_json()]
            }
            
        agent = agent_class(self.llm, tools, self.settings)
        from app.agents.prompts.prompt_utils import build_condensed_context
        condensed_analysis = build_condensed_context(state.get("analysis_result_json", "{}"), agent_type)
        
        context = {
            "repository_name": state["repository_name"],
            "repository_path": state["repository_path"],
            "analysis_result_json": condensed_analysis,
            "investigation_strategy": plan.strategy if plan else "Standard Investigation"
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
            event="Investigation completed, starting review"
        )
        return {
            "current_stage": "reviewing",
            "timeline_events": [event.model_dump_json()]
        }

    def reviewer_node(self, state: InvestigationState) -> dict:
        # Parse all agent reports
        agent_reports = {}
        for key in ["architecture_report", "execution_flow_report", "api_data_report", "setup_report"]:
            report_json = state.get(key)
            if report_json:
                report = AgentReport(**json.loads(report_json))
                agent_reports[report.agent_type] = report
                
        agent = ReviewerAgent(self.llm, self.settings)
        review_report = agent.review_all_reports(agent_reports)
        
        # Check for rejections to request revisions
        revision_requests = []
        for review in review_report.reviews:
            if review.verdict == ReviewVerdict.REJECTED:
                # If they want revisions, we can limit to 1 per finding.
                # For simplicity here, we assume if it's rejected and hasn't been revised, we request revision.
                req = RevisionRequest(
                    agent_type=review.agent_type,
                    finding_title=review.finding_title,
                    rejection_reason=review.reason,
                    original_finding=review.original_finding
                )
                revision_requests.append(req.model_dump_json())
                
        event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=AgentType.REVIEWER,
            event=f"Review completed. {review_report.total_approved} approved, {review_report.total_rejected} rejected."
        )
        
        # If no revisions, we'll go straight to synthesize. The workflow will handle the conditional edge.
        return {
            "review_report": review_report.model_dump_json(),
            "revision_requests": revision_requests,
            "timeline_events": [event.model_dump_json()]
        }
        
    def revision_node(self, state: InvestigationState) -> dict:
        # This is a simplified revision node. It just marks them as uncertain for now 
        # to avoid complex re-entrancy in the agent loops without a lot more scaffolding.
        # In a full implementation, this would loop back to specific agents.
        event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=AgentType.REVIEWER,
            event="Revisions requested, but automatic re-analysis is skipped. Marking as uncertain."
        )
        return {
            "current_stage": "revising",
            "timeline_events": [event.model_dump_json()],
            "revision_requests": [] # clear them so we don't loop forever
        }

    def synthesizer_node(self, state: InvestigationState) -> dict:
        event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=AgentType.SYNTHESIZER,
            event="Synthesizing onboarding guide..."
        )
        
        # Extract approved findings
        review_report_json = state.get("review_report")
        approved_findings = {
            AgentType.ARCHITECTURE: [],
            AgentType.EXECUTION_FLOW: [],
            AgentType.API_DATA: [],
            AgentType.SETUP: []
        }
        
        review_report = None
        if review_report_json:
             review_report = ReviewReport(**json.loads(review_report_json))
             for review in review_report.reviews:
                  if review.verdict == ReviewVerdict.APPROVED:
                       approved_findings[review.agent_type].append(review.original_finding)
                        
        # Fallback if no findings were approved (common with strict models)
        if not any(approved_findings.values()):
             logger.warning("No findings were approved by the reviewer. Falling back to all raw findings.")
             for key in ["architecture_report", "execution_flow_report", "api_data_report", "setup_report"]:
                  report_json = state.get(key)
                  if report_json:
                       report = AgentReport(**json.loads(report_json))
                       if report.findings:
                            approved_findings[report.agent_type].extend(report.findings)
                       
        analysis_result_json = state.get("analysis_result_json")
        analysis_result = None
        if analysis_result_json:
             analysis_result = AnalysisResult(**json.loads(analysis_result_json))
             
        # Map user role string to OnboardingRole enum
        role_str = state.get("user_role", self.settings.default_onboarding_role)
        try:
             role = OnboardingRole(role_str)
        except ValueError:
             role = OnboardingRole.FULL_STACK

        guide = None
        if analysis_result and review_report:
            agent = SynthesizerAgent(self.llm, self.settings)
            guide = agent.synthesize(approved_findings, review_report, analysis_result, role)
            
        done_event = TimelineEvent(
            timestamp=datetime.now(timezone.utc),
            agent_type=AgentType.SYNTHESIZER,
            event="Onboarding guide generated successfully."
        )

        return {
            "onboarding_guide": guide.model_dump_json() if guide else "",
            "current_stage": "done",
            "timeline_events": [event.model_dump_json(), done_event.model_dump_json()]
        }
