from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

class AgentType(str, Enum):
    SUPERVISOR = "SUPERVISOR"
    ARCHITECTURE = "ARCHITECTURE"
    EXECUTION_FLOW = "EXECUTION_FLOW"
    API_DATA = "API_DATA"
    SETUP = "SETUP"

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    REASONING = "REASONING"
    ACTING = "ACTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ToolResult(BaseModel):
    tool_name: str
    input_args: Dict[str, Any]
    output: str
    success: bool
    duration_seconds: float

    model_config = ConfigDict(frozen=True)

class Evidence(BaseModel):
    source_tool: str
    file_path: Optional[str] = None
    content: str
    relevance: str

    model_config = ConfigDict(frozen=True)

class AgentFinding(BaseModel):
    title: str
    description: str
    evidence: List[Evidence] = Field(default_factory=list)
    confidence: float
    category: str

    model_config = ConfigDict(frozen=True)

class InvestigationTask(BaseModel):
    task_id: str
    agent_type: AgentType
    description: str
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(frozen=True)

class TimelineEvent(BaseModel):
    timestamp: datetime
    agent_type: AgentType
    event: str
    detail: Optional[str] = None

    model_config = ConfigDict(frozen=True)

class AgentReport(BaseModel):
    agent_type: AgentType
    status: AgentStatus
    tasks: List[InvestigationTask] = Field(default_factory=list)
    findings: List[AgentFinding] = Field(default_factory=list)
    tool_calls: List[ToolResult] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = ConfigDict(frozen=True)

class InvestigationPlan(BaseModel):
    repository_name: str
    tasks: List[InvestigationTask]
    strategy: str
    created_at: datetime

    model_config = ConfigDict(frozen=True)

class InvestigationResult(BaseModel):
    plan: InvestigationPlan
    agent_reports: Dict[AgentType, AgentReport]
    timeline: List[TimelineEvent]
    started_at: datetime
    completed_at: datetime
    duration_seconds: float

    model_config = ConfigDict(frozen=True)
