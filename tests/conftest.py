import pytest
from pathlib import Path
from app.config.settings import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        ignored_directories=[".git", "node_modules", "__pycache__"],
        max_repo_size_mb=10,
        max_file_size_mb=1,
        binary_extensions=[".exe", ".bin"]
    )

@pytest.fixture
def sample_repo(tmp_path):
    # Create a small dummy repo for tests
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    
    (repo_dir / "main.py").write_text("print('hello')\n")
    (repo_dir / "requirements.txt").write_text("fastapi==0.100.0\n")
    
    src_dir = repo_dir / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
    
    git_dir = repo_dir / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("dummy")
    
    return repo_dir
