from app.analysis.stack_detector import StackDetector
from app.models.analysis_models import TechCategory

def test_stack_detector_python_fastapi(sample_repo, mock_settings):
    detector = StackDetector(mock_settings)
    stack = detector.analyse(sample_repo)
    
    # Check languages
    langs = stack.languages
    assert any(l.name == "Python" for l in langs)
    
    # Check frameworks
    frameworks = stack.frameworks
    assert any(f.name == "FastAPI" for f in frameworks)
    
    # Check package managers
    items = stack.items
    assert any(i.name == "pip" and i.category == TechCategory.PACKAGE_MANAGER for i in items)

def test_stack_detector_docker(tmp_path, mock_settings):
    # Setup
    (tmp_path / "Dockerfile").touch()
    (tmp_path / "docker-compose.yml").touch()
    
    detector = StackDetector(mock_settings)
    stack = detector.analyse(tmp_path)
    
    containers = [i for i in stack.items if i.category == TechCategory.CONTAINER]
    names = [c.name for c in containers]
    assert "Docker" in names
    assert "Docker Compose" in names

def test_stack_detector_javascript_react(tmp_path, mock_settings):
    # Setup
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0", "express": "^4.18"}}')
    (tmp_path / "app.js").touch()
    (tmp_path / "index.jsx").touch()
    
    detector = StackDetector(mock_settings)
    stack = detector.analyse(tmp_path)
    
    langs = [l.name for l in stack.languages]
    assert "JavaScript" in langs
    
    frameworks = [f.name for f in stack.frameworks]
    assert "React" in frameworks
    assert "Express" in frameworks
    
    pms = [p.name for p in stack.items if p.category == TechCategory.PACKAGE_MANAGER]
    assert "npm/yarn" in pms
