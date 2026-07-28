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
    source_tool: str = Field(description="Name of the tool used (e.g., read_file)")
    file_path: Optional[str] = Field(None, description="File path if applicable")
    content: str = Field(description="Snippet or summary of the evidence")
    relevance: str = Field(description="Why this proves the finding")

    model_config = ConfigDict(frozen=True)

class AgentFinding(BaseModel):
    title: str = Field(description="Short title of the finding")
    description: str = Field(description="Detailed explanation of the finding")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence supporting the finding")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    category: str = Field(description="Category of the finding")

    model_config = ConfigDict(frozen=True)

class FindingsOutput(BaseModel):
    findings: List[AgentFinding] = Field(description="List of all findings extracted from the text")
    
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
