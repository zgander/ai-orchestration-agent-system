import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.models.investigation_models import AgentFinding, AgentType
from app.models.review_models import ReviewReport
from app.models.analysis_models import AnalysisResult, RepositoryTree, FileNode, TechStack, SymbolIndex, DependencyGraphModel, RepositoryStatistics
from app.models.repository import RepositoryInfo, RepositorySource, SourceType
from app.models.onboarding_models import OnboardingRole
from app.agents.synthesizer_agent import SynthesizerAgent
from app.config.settings import Settings

@pytest.fixture
def mock_llm():
    llm = Mock()
    mock_structured = Mock()
    mock_pipe = Mock()
    
    # We'll just return generic outputs for all extraction types
    class GenericOutput:
        description = "A great app"
        languages = ["Python"]
        frameworks = ["FastAPI"]
        architecture_style = "Microservices"
        database = "PostgreSQL"
        testing_framework = "pytest"
        explanation = "High level explanation"
        diagram = "graph TD\nA-->B"
        folders = []
        important_files = []
        flows = []
        days = []
        
        from app.models.onboarding_models import SetupGuide
        setup = SetupGuide(
            installation_steps=[], 
            environment_variables=[], 
            run_commands=[], 
            testing_commands=[], 
            docker_instructions=None, 
            evidence=[]
        )
        
    mock_pipe.invoke.return_value = GenericOutput()
    
    with patch('langchain_core.prompts.ChatPromptTemplate.__or__', return_value=mock_pipe):
        llm.with_structured_output.return_value = mock_structured
        yield llm

@pytest.fixture
def settings():
    return Settings(enable_mermaid_diagrams=True)

@pytest.fixture
def dummy_analysis_result(tmp_path):
    return AnalysisResult(
        repository_info=RepositoryInfo(
            name="test-repo",
            source=RepositorySource(source_type=SourceType.ZIP, local_path=str(tmp_path)),
            root_path=str(tmp_path),
            cloned_at=datetime.now(timezone.utc),
            size_bytes=100
        ),
        tree=RepositoryTree(root=FileNode(name="root", path=str(tmp_path), is_dir=True, size=0, depth=0), total_files=0, total_dirs=0, max_depth=0),
        tech_stack=TechStack(items=[]),
        entry_points=[],
        api_endpoints=[],
        env_variables=[],
        dependency_graph=DependencyGraphModel(nodes=[], edges=[], connected_components=0, most_connected=[]),
        symbol_index=SymbolIndex(symbols=[]),
        statistics=RepositoryStatistics(total_files=0, total_dirs=0, total_source_files=0, languages_breakdown={}, largest_dirs={}),
        analysed_at=datetime.now(timezone.utc),
        duration_seconds=1.0
    )

def test_synthesize_with_approved_findings(mock_llm, settings, dummy_analysis_result):
    agent = SynthesizerAgent(mock_llm, settings)
    
    approved = {
        AgentType.ARCHITECTURE: [
             AgentFinding(title="Arch Finding", description="Uses MVC", category="Arch", confidence=0.9, evidence=[])
        ]
    }
    
    review_report = ReviewReport(
        reviews=[], total_approved=1, total_rejected=0, total_uncertain=0, overall_confidence=0.9, revision_count=0, reviewed_at=datetime.now(timezone.utc)
    )
    
    guide = agent.synthesize(approved, review_report, dummy_analysis_result, OnboardingRole.BACKEND)
    
    assert guide is not None
    assert guide.role == OnboardingRole.BACKEND
    assert guide.repository_overview.name == "test-repo"
    assert guide.architecture_explanation == "High level explanation"
    assert guide.architecture_diagram == "graph TD\nA-->B"
