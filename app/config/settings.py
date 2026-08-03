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
    ollama_model: str = "llama3.2:3b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    google_api_key: str = ""
    google_model: str = "gemini-2.5-flash"
    temperature: float = 0
    max_tokens: int = 2048

    # Agent Settings
    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 120
    parallel_execution: bool = True
    max_parallel_agents: int = 2

    # --- Phase 3 Additions ---
    # Reviewer
    max_reviewer_iterations: int = 1
    min_confidence_threshold: float = 0.3
    evidence_required: bool = True

    # Synthesizer
    enable_mermaid_diagrams: bool = True
    default_onboarding_role: str = "Full Stack Developer"

    # --- Phase 4/5: Chat ---
    chat_cache_dir: str = ".repolens_cache/chat_sessions"
    chat_memory_window_size: int = 20
    chat_session_max_age_hours: int = 48
    max_knowledge_fragments: int = 5
    enable_reinvestigation: bool = False

    # --- Phase 5 Additions ---
    # UI and Appearance
    theme: str = "light"  # light or dark
    diagram_style: str = "default"  # default, neutral, dark
    
    # Export and Search
    export_format: str = "MARKDOWN"
    max_search_results: int = 20
    
    # Caching
    cache_max_age_hours: int = 168  # 7 days for repository history
    
    # Advanced / Debug
    debug_mode: bool = False
    enable_ai_explain: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="REPOLENS_")

settings = Settings()
