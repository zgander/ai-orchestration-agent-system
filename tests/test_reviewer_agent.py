import pytest
from unittest.mock import Mock, patch
from app.models.investigation_models import AgentFinding, AgentType, Evidence
from app.models.review_models import ReviewVerdict
from app.agents.reviewer_agent import ReviewerAgent
from app.config.settings import Settings

@pytest.fixture
def mock_llm():
    llm = Mock()
    mock_structured = Mock()
    
    # Setup the mock output
    class MockOutput:
        verdict = ReviewVerdict.APPROVED
        reason = "Looks good"
        confidence = 0.95
        
    mock_structured.invoke.return_value = MockOutput()
    
    # We need to mock the pipe operation: prompt | structured_llm
    mock_pipe = Mock()
    mock_pipe.invoke.return_value = MockOutput()
    
    # When __or__ (|) is called on the prompt template, return mock_pipe
    with patch('langchain_core.prompts.ChatPromptTemplate.__or__', return_value=mock_pipe):
        # We also need to mock with_structured_output since it's called in the code
        llm.with_structured_output.return_value = mock_structured
        yield llm

@pytest.fixture
def settings():
    return Settings(evidence_required=True, min_confidence_threshold=0.3)

def test_approve_finding_with_evidence(mock_llm, settings):
    agent = ReviewerAgent(mock_llm, settings)
    
    finding = AgentFinding(
        title="Test Finding",
        description="A valid finding",
        category="Architecture",
        confidence=0.8,
        evidence=[Evidence(source_tool="test", content="test data", relevance="test")]
    )
    
    review = agent.review_finding(finding, AgentType.ARCHITECTURE)
    
    assert review.verdict == ReviewVerdict.APPROVED
    assert review.finding_title == "Test Finding"

def test_reject_finding_without_evidence(mock_llm, settings):
    agent = ReviewerAgent(mock_llm, settings)
    
    finding = AgentFinding(
        title="Test Finding No Evidence",
        description="An invalid finding",
        category="Architecture",
        confidence=0.8,
        evidence=[]
    )
    
    review = agent.review_finding(finding, AgentType.ARCHITECTURE)
    
    # Should auto-reject without calling LLM
    assert review.verdict == ReviewVerdict.REJECTED
    assert "No evidence" in review.reason
    assert not mock_llm.with_structured_output.called

def test_reject_finding_low_confidence(mock_llm, settings):
    agent = ReviewerAgent(mock_llm, settings)
    
    finding = AgentFinding(
        title="Test Finding Low Conf",
        description="A low confidence finding",
        category="Architecture",
        confidence=0.2, # below threshold 0.3
        evidence=[Evidence(source_tool="test", content="test data", relevance="test")]
    )
    
    review = agent.review_finding(finding, AgentType.ARCHITECTURE)
    
    assert review.verdict == ReviewVerdict.REJECTED
    assert "below minimum threshold" in review.reason

def test_review_all_reports(mock_llm, settings):
    agent = ReviewerAgent(mock_llm, settings)
    
    from app.models.investigation_models import AgentReport, AgentStatus
    from datetime import datetime, timezone
    
    report1 = AgentReport(
        agent_type=AgentType.ARCHITECTURE,
        status=AgentStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        findings=[
             AgentFinding(
                title="Finding 1",
                description="Desc 1",
                category="Cat 1",
                confidence=0.9,
                evidence=[Evidence(source_tool="t", content="c", relevance="r")]
            )
        ]
    )
    
    reports = {AgentType.ARCHITECTURE: report1}
    
    review_report = agent.review_all_reports(reports)
    
    assert len(review_report.reviews) == 1
    assert review_report.total_approved == 1
    assert review_report.total_rejected == 0
