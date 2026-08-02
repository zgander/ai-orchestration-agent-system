from typing import List, Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from enum import Enum

class RepositoryInvestigationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
class RepositoryMetadata(BaseModel):
    name: str = Field(description="Repository name")
    url: Optional[str] = Field(None, description="Source URL if applicable")
    source_type: str = Field(description="GITHUB or ZIP")
    root_path: str = Field(description="Path to repository on disk")
    tech_stack_summary: Dict[str, List[str]] = Field(default_factory=dict, description="Summary of tech stack")
    analysed_at: datetime = Field(description="When the repository was first ingested and analysed")
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the repo was last viewed")
    investigation_status: RepositoryInvestigationStatus = Field(default_factory=lambda: RepositoryInvestigationStatus.NOT_STARTED)
    pinned: bool = Field(default=False, description="Whether this repository is pinned in the UI")
    size_bytes: int = Field(default=0, description="Size of the repository in bytes")
    
    model_config = ConfigDict(frozen=True)

class PerformanceMetrics(BaseModel):
    recorded_at: datetime
    repo_load_time_seconds: float = 0.0
    analysis_duration_seconds: float = 0.0
    agent_durations: Dict[str, float] = Field(default_factory=dict)
    reviewer_duration_seconds: float = 0.0
    synthesis_duration_seconds: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    chat_latencies: List[float] = Field(default_factory=list)

class SearchResultType(str, Enum):
    FILE = "FILE"
    FOLDER = "FOLDER"
    SYMBOL = "SYMBOL"
    API = "API"
    EXECUTION_FLOW = "EXECUTION_FLOW"
    ARCHITECTURE = "ARCHITECTURE"
    DOCUMENTATION_GAP = "DOCUMENTATION_GAP"
    CHAT_HISTORY = "CHAT_HISTORY"
    ONBOARDING = "ONBOARDING"

class GlobalSearchResult(BaseModel):
    title: str
    snippet: str
    url_fragment: str
    result_type: SearchResultType
    source_section: Optional[str] = None
    relevance: float = 1.0

class ExportFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    BUNDLE = "BUNDLE"

class ExportConfig(BaseModel):
    format: ExportFormat
    sections: List[str] = Field(default_factory=lambda: ["Architecture", "Folder Guide", "Execution Flows", "API Explorer", "Setup & Environment"])
    include_evidence: bool = True
    include_diagrams: bool = True
