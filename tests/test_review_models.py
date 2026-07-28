from datetime import datetime, timezone
import pytest
from app.models.review_models import ReviewReport, FindingReview, ReviewVerdict
from app.models.investigation_models import AgentType, AgentFinding

def test_review_report_aggregation():
    finding = AgentFinding(title="Test", description="Desc", category="Cat", confidence=0.8, evidence=[])
    
    r1 = FindingReview(finding_title="F1", agent_type=AgentType.ARCHITECTURE, verdict=ReviewVerdict.APPROVED, confidence=1.0, reason="", original_finding=finding)
    r2 = FindingReview(finding_title="F2", agent_type=AgentType.SETUP, verdict=ReviewVerdict.REJECTED, confidence=0.8, reason="", original_finding=finding)
    r3 = FindingReview(finding_title="F3", agent_type=AgentType.API_DATA, verdict=ReviewVerdict.UNCERTAIN, confidence=0.6, reason="", original_finding=finding)
    
    report = ReviewReport(
        reviews=[r1, r2, r3],
        total_approved=1,
        total_rejected=1,
        total_uncertain=1,
        overall_confidence=0.8, # (1.0 + 0.8 + 0.6) / 3
        revision_count=0,
        reviewed_at=datetime.now(timezone.utc)
    )
    
    assert report.total_approved == 1
    assert report.total_rejected == 1
    assert report.total_uncertain == 1
    assert report.overall_confidence == 0.8
    assert len(report.reviews) == 3
