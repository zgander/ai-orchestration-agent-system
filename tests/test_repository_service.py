from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone
from app.services.repository_service import RepositoryService
from app.models.repository import SourceType, RepositoryInfo, RepositorySource

@patch('app.services.github_service.GitHubService.clone')
def test_repository_service_analyse(mock_clone, sample_repo, mock_settings):
    mock_clone.return_value = sample_repo
    service = RepositoryService(mock_settings)
    
    # Create dummy repo info
    repo_info = service.ingest(SourceType.GITHUB, "https://github.com/dummy/dummy", sample_repo)

@patch('app.services.github_service.GitHubService.clone')
def test_repository_service_ingest_github(mock_clone, mock_settings, tmp_path):
    mock_clone.return_value = tmp_path
    service = RepositoryService(mock_settings)
    
    # Setup some fake files to pass size check
    (tmp_path / "test.txt").write_text("hello")
    
    info = service.ingest(SourceType.GITHUB, "https://github.com/test/repo", tmp_path)
    
    assert info.name == "repo"
    assert info.source.source_type == SourceType.GITHUB
    assert info.size_bytes > 0

def test_repository_service_full_flow(sample_repo, mock_settings):
    # We can just test analyse directly
    service = RepositoryService(mock_settings)
    
    repo_info = RepositoryInfo(
        name="test",
        source=RepositorySource(source_type=SourceType.GITHUB, local_path=str(sample_repo)),
        root_path=str(sample_repo),
        cloned_at=datetime.now(timezone.utc),
        size_bytes=100
    )
        
    result = service.analyse(repo_info)
    
    assert result.tree.total_files > 0
    assert result.duration_seconds > 0
