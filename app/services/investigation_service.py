import json
from datetime import datetime, timezone
from typing import Optional, Callable
import time

from langchain_core.language_models.chat_models import BaseChatModel

from app.models.analysis_models import AnalysisResult
from app.models.investigation_models import InvestigationResult, InvestigationPlan, AgentReport, TimelineEvent
from app.graph.workflow import build_investigation_workflow
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

from app.utils.llm_factory import LLMFactory

class InvestigationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMFactory.get_llm(self.settings)
        self.workflow = build_investigation_workflow(self.llm, settings)

    def investigate(
        self,
        analysis_result: AnalysisResult,
        user_role: str,
        user_question: str,
        progress_callback: Optional[Callable] = None
    ) -> InvestigationResult:
        start_time = datetime.now(timezone.utc)
        start_ts = time.time()
        
        # Initial state
        initial_state = {
            "repository_name": analysis_result.repository_info.name,
            "repository_path": str(analysis_result.repository_info.root_path),
            "analysis_result_json": analysis_result.model_dump_json(),
            "user_role": user_role,
            "user_question": user_question,
            "timeline_events": [],
            "errors": []
        }
        
        # Execute workflow
        final_state = initial_state
        for state in self.workflow.stream(initial_state, stream_mode="values"):
            final_state = state
            if progress_callback and "timeline_events" in state:
                events = [TimelineEvent(**json.loads(ev)) for ev in state["timeline_events"]]
                progress_callback(events)
                
        end_time = datetime.now(timezone.utc)
        
        # Parse final state
        plan = None
        if final_state.get("investigation_plan"):
            plan = InvestigationPlan(**json.loads(final_state["investigation_plan"]))
            
        agent_reports = {}
        for key in ["architecture_report", "execution_flow_report", "api_data_report", "setup_report"]:
            report_json = final_state.get(key)
            if report_json:
                report = AgentReport(**json.loads(report_json))
                agent_reports[report.agent_type] = report
                
        timeline = [TimelineEvent(**json.loads(ev)) for ev in final_state.get("timeline_events", [])]
        
        from app.models.review_models import ReviewReport
        review_report = None
        if final_state.get("review_report"):
             review_report = ReviewReport(**json.loads(final_state["review_report"]))

        from app.models.onboarding_models import OnboardingGuide
        onboarding_guide = None
        if final_state.get("onboarding_guide"):
             onboarding_guide = OnboardingGuide(**json.loads(final_state["onboarding_guide"]))
        
        return InvestigationResult(
            plan=plan,
            agent_reports=agent_reports,
            timeline=timeline,
            started_at=start_time,
            completed_at=end_time,
            duration_seconds=time.time() - start_ts,
            review_report=review_report,
            onboarding_guide=onboarding_guide
        )
