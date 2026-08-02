from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.investigation_models import Evidence


class HealthScore(BaseModel):
    category: str
    score: str
    explanation: str

    model_config = ConfigDict(frozen=True)

class ArchitectureLayer(BaseModel):
    name: str
    purpose: str
    components: List[str]
    order: int

    model_config = ConfigDict(frozen=True)

class ComponentCard(BaseModel):
    name: str
    purpose: str
    responsibilities: List[str]
    consumes: List[str]
    produces: List[str]
    dependencies: List[str]
    used_by: List[str]

    model_config = ConfigDict(frozen=True)

class DependencyInsight(BaseModel):
    insight_type: str
    module: str
    explanation: str

    model_config = ConfigDict(frozen=True)

class OnboardingRole(str, Enum):
    BACKEND = "Backend Developer"
    FRONTEND = "Frontend Developer"
    FULL_STACK = "Full Stack Developer"
    QA = "QA Engineer"
    DEVOPS = "DevOps Engineer"


class RepositoryOverview(BaseModel):
    name: str
    description: str
    languages: List[str]
    frameworks: List[str]
    architecture_style: str
    database: Optional[str] = None
    testing_framework: Optional[str] = None
    project_type: str = "Unknown"
    primary_purpose: str = "Unknown"
    main_components: List[str] = Field(default_factory=list)
    estimated_complexity: str = "Unknown"
    estimated_learning_time_minutes: int = 0
    statistics: Dict[str, Any]

    model_config = ConfigDict(frozen=True)


class FolderExplanation(BaseModel):
    path: str
    purpose: str
    importance: str
    read_first: bool
    evidence: List[Evidence] = []

    model_config = ConfigDict(frozen=True)


class ImportantFile(BaseModel):
    rank: int
    file_path: str
    purpose: str
    why_it_matters: str
    dependencies: List[str]
    evidence: List[Evidence] = []

    model_config = ConfigDict(frozen=True)


class ExecutionFlow(BaseModel):
    name: str
    steps: List[Dict[str, str]]
    mermaid_diagram: Optional[str] = None
    evidence: List[Evidence] = []
    confidence: float = 1.0
    supporting_files: List[str] = Field(default_factory=list)
    flow_type: str = "Unknown"

    model_config = ConfigDict(frozen=True)


class APIEndpointGuide(BaseModel):
    method: str
    path: str
    purpose: str
    request_format: Optional[str] = None
    response_format: Optional[str] = None
    handler_file: str
    handler_function: str
    evidence: List[Evidence] = []

    model_config = ConfigDict(frozen=True)


class ReadingOrderDay(BaseModel):
    day: int
    theme: str
    topics: List[str]
    files: List[str]

    model_config = ConfigDict(frozen=True)


class DocumentationGap(BaseModel):
    gap_type: str
    description: str
    severity: str
    affected_path: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class SetupGuide(BaseModel):
    installation_steps: List[str]
    environment_variables: List[Dict[str, str]]
    run_commands: List[Dict[str, str]]
    docker_instructions: Optional[str] = None
    testing_commands: List[str]
    evidence: List[Evidence] = []

    model_config = ConfigDict(frozen=True)


class ConfidenceIndicator(BaseModel):
    section: str
    confidence: float
    note: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class OnboardingGuide(BaseModel):
    role: OnboardingRole
    repository_overview: RepositoryOverview
    architecture_explanation: str
    architecture_diagram: Optional[str] = None
    folder_guide: List[FolderExplanation]
    important_files: List[ImportantFile]
    execution_flows: List[ExecutionFlow]
    api_explorer: List[APIEndpointGuide]
    reading_order: List[ReadingOrderDay]
    setup_guide: SetupGuide
    documentation_gaps: List[DocumentationGap]
    confidence_indicators: List[ConfidenceIndicator]
    mental_model: str
    ai_insights: List[str] = Field(default_factory=list)
    common_pitfalls: List[str] = Field(default_factory=list)
    repository_health: List[HealthScore] = Field(default_factory=list)
    architecture_layers: List[ArchitectureLayer] = Field(default_factory=list)
    component_cards: List[ComponentCard] = Field(default_factory=list)
    dependency_insights: List[DependencyInsight] = Field(default_factory=list)
    generated_at: datetime

    model_config = ConfigDict(frozen=True)
