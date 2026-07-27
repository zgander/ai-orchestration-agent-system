from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import tempfile


class Settings(BaseSettings):
    # Security
    ignored_directories: List[str] = [
        ".git", "node_modules", "dist", "build", "coverage", 
        "venv", ".venv", "__pycache__", ".cache", ".next", ".idea", ".vscode"
    ]
    max_repo_size_mb: int = 500
    max_file_size_mb: int = 10
    binary_extensions: List[str] = [
        ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite",
        ".jpg", ".jpeg", ".png", ".gif", ".ico", ".webp", ".pdf", ".mp4", ".zip", ".tar", ".gz"
    ]

    # Paths
    temp_directory: str = tempfile.gettempdir()

    # Logging
    log_level: str = "INFO"

    # --- Phase 2 Additions ---
    # LLM Provider
    llm_provider: str = "ollama"
    ollama_model: str = "gpt-oss:120b-cloud"
    ollama_base_url: str = "http://127.0.0.1:11434"
    temperature: float = 0
    max_tokens: int = 4096

    # Agent Settings
    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 120
    parallel_execution: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="REPOLENS_")

settings = Settings()
