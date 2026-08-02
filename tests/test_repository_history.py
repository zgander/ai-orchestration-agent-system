import pytest
import shutil
from pathlib import Path
from datetime import datetime, timezone
from app.services.repository_history import RepositoryHistoryService
from app.models.history_models import RepositoryMetadata, RepositoryInvestigationStatus

@pytest.fixture
def history_service(tmp_path):
    # Override the history directory for testing
    service = RepositoryHistoryService()
    service.history_dir = tmp_path / "history"
    service.history_dir.mkdir()
    return service

def test_save_and_get_repository(history_service):
    metadata = RepositoryMetadata(
        name="test-repo",
        url="https://github.com/test/repo",
        source_type="GITHUB",
        root_path="/tmp/test-repo",
        tech_stack_summary={"languages": ["Python"]},
        analysed_at=datetime.now(timezone.utc),
        investigation_status=RepositoryInvestigationStatus.COMPLETED
    )
    
    history_service.save_repository(metadata)
    
    loaded = history_service.get_repository("test-repo")
    assert loaded is not None
    assert loaded.name == "test-repo"
    assert "Python" in loaded.tech_stack_summary["languages"]
    
def test_search_repositories(history_service):
    m1 = RepositoryMetadata(
        name="frontend-app",
        source_type="GITHUB",
        root_path="/tmp/f",
        tech_stack_summary={"languages": ["TypeScript"]},
        analysed_at=datetime.now(timezone.utc)
    )
    m2 = RepositoryMetadata(
        name="backend-api",
        source_type="GITHUB",
        root_path="/tmp/b",
        tech_stack_summary={"languages": ["Python"]},
        analysed_at=datetime.now(timezone.utc)
    )
    history_service.save_repository(m1)
    history_service.save_repository(m2)
    
    results = history_service.search_repositories("frontend")
    assert len(results) == 1
    assert results[0].name == "frontend-app"
    
    results_tech = history_service.search_repositories("Python")
    assert len(results_tech) == 1
    assert results_tech[0].name == "backend-api"

def test_delete_repository(history_service):
    m1 = RepositoryMetadata(
        name="test-repo",
        source_type="GITHUB",
        root_path="/tmp/t",
        analysed_at=datetime.now(timezone.utc)
    )
    history_service.save_repository(m1)
    assert history_service.get_repository("test-repo") is not None
    
    success = history_service.delete_repository("test-repo")
    assert success is True
    assert history_service.get_repository("test-repo") is None
