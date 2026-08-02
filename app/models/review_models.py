from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.models.investigation_models import AgentFinding, AgentType


class ReviewVerdict(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"


class FindingReview(BaseModel):
    finding_title: str
    agent_type: AgentType
    verdict: ReviewVerdict
    confidence: float
    reason: str
    revision_requested: bool = False
    revision_completed: bool = False
    original_finding: AgentFinding
    revised_finding: Optional[AgentFinding] = None

    model_config = ConfigDict(frozen=True)


class ReviewReport(BaseModel):
    reviews: List[FindingReview]
    total_approved: int
    total_rejected: int
    total_uncertain: int
    overall_confidence: float
    revision_count: int
    reviewed_at: datetime

    model_config = ConfigDict(frozen=True)


class RevisionRequest(BaseModel):
    agent_type: AgentType
    finding_title: str
    rejection_reason: str
    original_finding: AgentFinding

    model_config = ConfigDict(frozen=True)
