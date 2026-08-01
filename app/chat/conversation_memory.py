import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.models.chat_models import ChatSession, ChatMessage
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConversationMemory:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache_dir = Path(self.settings.chat_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_old_sessions()

    def get_or_create_session(self, session_id: Optional[str], repository_name: str) -> ChatSession:
        if session_id:
            session = self.load_session(session_id, repository_name)
            if session:
                return session
                
        # Create new session
        new_session = ChatSession(
            session_id=str(uuid.uuid4()),
            repository_name=repository_name,
            messages=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.save_session(new_session)
        return new_session

    def load_session(self, session_id: str, repository_name: str) -> Optional[ChatSession]:
        repo_dir = self.cache_dir / repository_name
        session_file = repo_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
            
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ChatSession(**data)
        except Exception as e:
            logger.error(f"Failed to load chat session {session_id}: {e}")
            return None

    def save_session(self, session: ChatSession) -> None:
        repo_dir = self.cache_dir / session.repository_name
        repo_dir.mkdir(parents=True, exist_ok=True)
        session_file = repo_dir / f"{session.session_id}.json"
        
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                f.write(session.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to save chat session {session.session_id}: {e}")

    def add_messages(self, session: ChatSession, new_messages: List[ChatMessage]) -> ChatSession:
        all_messages = session.messages + new_messages
        
        # Apply sliding window
        window_size = self.settings.chat_memory_window_size
        if len(all_messages) > window_size:
            all_messages = all_messages[-window_size:]
            
        updated_session = ChatSession(
            session_id=session.session_id,
            repository_name=session.repository_name,
            messages=all_messages,
            created_at=session.created_at,
            updated_at=datetime.now(timezone.utc)
        )
        self.save_session(updated_session)
        return updated_session

    def get_session_history(self, repository_name: str) -> List[ChatSession]:
        repo_dir = self.cache_dir / repository_name
        if not repo_dir.exists():
            return []
            
        sessions = []
        for file_path in repo_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(ChatSession(**data))
            except Exception as e:
                logger.error(f"Failed to read session file {file_path}: {e}")
                
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def _cleanup_old_sessions(self) -> None:
        # Check all repos
        if not self.cache_dir.exists():
            return
            
        max_age_seconds = self.settings.chat_session_max_age_hours * 3600
        now = datetime.now(timezone.utc)
        
        for repo_dir in self.cache_dir.iterdir():
            if repo_dir.is_dir():
                for file_path in repo_dir.glob("*.json"):
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                        age = (now - mtime).total_seconds()
                        if age > max_age_seconds:
                            file_path.unlink()
                            logger.info(f"Cleaned up old chat session: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {file_path}: {e}")
