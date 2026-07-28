import pytest
from pathlib import Path
from datetime import datetime, timezone
from app.analysis.gap_detector import GapDetector
from app.models.analysis_models import AnalysisResult, RepositoryTree, FileNode, TechStack, SymbolIndex, DependencyGraphModel, RepositoryStatistics, EnvVariable, APIEndpoint, TechStackItem, TechCategory
from app.models.repository import RepositoryInfo, RepositorySource, SourceType
from app.config.settings import Settings

@pytest.fixture
def temp_repo(tmp_path):
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()
    return repo_dir

@pytest.fixture
def dummy_analysis_result():
    return AnalysisResult(
        repository_info=RepositoryInfo(
            name="test-repo",
            source=RepositorySource(source_type=SourceType.ZIP, local_path="/tmp"),
            root_path="/tmp",
            cloned_at=datetime.now(timezone.utc),
            size_bytes=100
        ),
        tree=RepositoryTree(root=FileNode(name="root", path="/", is_dir=True, size=0, depth=0), total_files=0, total_dirs=0, max_depth=0),
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

def test_detect_missing_readme(temp_repo, dummy_analysis_result):
    detector = GapDetector(Settings())
    gaps = detector.detect(temp_repo, dummy_analysis_result)
    
    assert any(g.gap_type == "Missing README" for g in gaps)
    
    # Create README and test again
    (temp_repo / "README.md").write_text("# Hello")
    gaps = detector.detect(temp_repo, dummy_analysis_result)
    
    assert not any(g.gap_type == "Missing README" for g in gaps)

def test_detect_missing_env_example(temp_repo, dummy_analysis_result):
    # Add env var to analysis result
    dummy_analysis_result_with_env = dummy_analysis_result.model_copy(update={
        "env_variables": [EnvVariable(name="API_KEY", file_path="main.py", line_number=1, access_method="os.environ")]
    })
    
    detector = GapDetector(Settings())
    gaps = detector.detect(temp_repo, dummy_analysis_result_with_env)
    
    assert any(g.gap_type == "Missing .env.example" for g in gaps)
    
    (temp_repo / ".env.example").write_text("API_KEY=xxx")
    gaps = detector.detect(temp_repo, dummy_analysis_result_with_env)
    
    assert not any(g.gap_type == "Missing .env.example" for g in gaps)

def test_detect_missing_tests(temp_repo, dummy_analysis_result):
    detector = GapDetector(Settings())
    gaps = detector.detect(temp_repo, dummy_analysis_result)
    
    assert any(g.gap_type == "Missing Tests" for g in gaps)
    
    dummy_analysis_result_with_tests = dummy_analysis_result.model_copy(update={
        "tech_stack": TechStack(items=[TechStackItem(name="pytest", category=TechCategory.TESTING, confidence=1.0, evidence_files=[])])
    })
    
    gaps = detector.detect(temp_repo, dummy_analysis_result_with_tests)
    assert not any(g.gap_type == "Missing Tests" for g in gaps)

def test_detect_undocumented_apis(temp_repo, dummy_analysis_result):
    # Create a dummy python file
    (temp_repo / "main.py").write_text("def hello():\n    return 'hi'\n")
    
    dummy_analysis_result_with_api = dummy_analysis_result.model_copy(update={
        "api_endpoints": [APIEndpoint(method="GET", path="/hello", handler_name="hello", file_path="main.py", line_number=1, framework="FastAPI")]
    })
    
    detector = GapDetector(Settings())
    gaps = detector.detect(temp_repo, dummy_analysis_result_with_api)
    
    # The file has no docstring
    assert any(g.gap_type == "Undocumented APIs" for g in gaps)
    
    # Add docstring
    (temp_repo / "main.py").write_text('def hello():\n    """Hello API"""\n    return "hi"\n')
    
    gaps = detector.detect(temp_repo, dummy_analysis_result_with_api)
    assert not any(g.gap_type == "Undocumented APIs" for g in gaps)
