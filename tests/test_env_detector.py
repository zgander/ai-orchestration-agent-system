from app.analysis.env_detector import EnvDetector

def test_env_detector(tmp_path, mock_settings):
    # Setup .env file
    env_file = tmp_path / ".env.example"
    env_file.write_text("""
# Database Config
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=
""")

    # Setup Python file
    py_file = tmp_path / "config.py"
    py_file.write_text("""
import os
from pydantic_settings import BaseSettings

api_key = os.getenv("API_KEY", "default")
db_pass = os.environ.get("DB_PASS")
db_user = os.environ["DB_USER"]

class AppSettings(BaseSettings):
    redis_url: str
    redis_port: int = 6379
""")

    # Setup JS file
    js_file = tmp_path / "app.js"
    js_file.write_text("""
const port = process.env.PORT || 3000;
const host = process.env['HOST_NAME'];
""")

    detector = EnvDetector(mock_settings)
    vars = detector.analyse(tmp_path)
    
    names = {v.name for v in vars}
    
    # Check .env
    assert "DB_HOST" in names
    assert "DB_PORT" in names
    assert "SECRET_KEY" in names
    
    # Check Python os.environ
    assert "API_KEY" in names
    assert "DB_PASS" in names
    assert "DB_USER" in names
    
    # Check Python BaseSettings
    assert "redis_url" in names
    assert "redis_port" in names
    
    # Check JS process.env
    assert "PORT" in names
    assert "HOST_NAME" in names
