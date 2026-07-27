from typing import TypedDict, List
import operator
from typing_extensions import Annotated

class InvestigationState(TypedDict):
    # Input context (set once at start)
    repository_name: str
    repository_path: str
    analysis_result_json: str              # Serialised AnalysisResult from Phase 1
    user_role: str
    user_question: str

    # Supervisor output
    investigation_plan: str                # Serialised InvestigationPlan

    # Agent reports (accumulated)
    architecture_report: str               # Serialised AgentReport
    execution_flow_report: str
    api_data_report: str
    setup_report: str

    # Timeline (append-only list)
    # We use Annotated with operator.add so LangGraph appends to the list instead of overwriting it
    timeline_events: Annotated[List[str], operator.add]             # List of serialised TimelineEvent JSONs

    # Control flow
    current_stage: str                     # "supervisor" | "investigate" | "merge" | "done"
    errors: Annotated[List[str], operator.add]
