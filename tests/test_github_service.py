import pytest
from app.services.github_service import GitHubService, InvalidURLError

def test_validate_url():
    service = GitHubService()
    
    assert service.validate_url("https://github.com/tiangolo/fastapi") is True
    assert service.validate_url("http://github.com/user/repo") is True
    assert service.validate_url("https://github.com/user/repo.git") is True
    assert service.validate_url("https://www.github.com/user/repo") is True
    
    assert service.validate_url("https://gitlab.com/user/repo") is False
    assert service.validate_url("github.com/user/repo") is False
    assert service.validate_url("not_a_url") is False

def test_clone_invalid_url(tmp_path):
    service = GitHubService()
    with pytest.raises(InvalidURLError):
        service.clone("https://gitlab.com/user/repo", tmp_path / "target")
