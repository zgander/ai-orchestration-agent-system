import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.investigation_models import InvestigationResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_DIR = Path(".repolens_cache/investigations")

def _get_cache_key(repo_name: str, user_role: str, user_question: str) -> str:
    # A simple hash of the core parameters
    data = f"{repo_name}_{user_role}_{user_question}"
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def save_investigation_result(repo_name: str, user_role: str, user_question: str, result: InvestigationResult) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = _get_cache_key(repo_name, user_role, user_question)
        cache_file = CACHE_DIR / f"{key}.json"
        
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
            
        logger.info(f"Saved investigation cache to {cache_file}")
    except Exception as e:
        logger.error(f"Failed to save investigation cache: {e}")

def load_investigation_result(repo_name: str, user_role: str, user_question: str, max_age_hours: int = 24) -> Optional[InvestigationResult]:
    try:
        key = _get_cache_key(repo_name, user_role, user_question)
        cache_file = CACHE_DIR / f"{key}.json"
        
        if not cache_file.exists():
            return None
            
        # Check age
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(timezone.utc) - mtime
        
        if age.total_seconds() > max_age_hours * 3600:
            logger.info(f"Cache {cache_file} is too old ({age.total_seconds() / 3600:.1f}h). Expiring.")
            cache_file.unlink()
            return None
            
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        result = InvestigationResult(**data)
        logger.info(f"Loaded investigation result from cache: {cache_file}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to load investigation cache: {e}")
        return None
