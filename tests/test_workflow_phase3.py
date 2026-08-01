import pytest
from unittest.mock import Mock
from app.graph.workflow import build_investigation_workflow
from app.config.settings import Settings

@pytest.fixture
def settings():
    return Settings(parallel_execution=False)

def test_workflow_includes_phase3_nodes(settings):
    llm = Mock()
    workflow = build_investigation_workflow(llm, settings)
    
    # We can check nodes in the compiled graph
    assert "reviewer_node" in workflow.nodes
    assert "revision_node" in workflow.nodes
    assert "synthesizer_node" in workflow.nodes

def test_workflow_edges(settings):
    # This just ensures we can compile without cycle errors or missing edge errors
    llm = Mock()
    workflow = build_investigation_workflow(llm, settings)
    assert workflow is not None
