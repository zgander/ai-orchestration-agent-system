import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import shutil

from app.models.history_models import RepositoryMetadata

class RepositoryHistoryService:
    def __init__(self):
        # We store metadata in .repolens_cache/repository_history
        self.history_dir = Path(".repolens_cache/repository_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
    def save_repository(self, metadata: RepositoryMetadata) -> None:
        """Saves or updates repository metadata."""
        file_path = self.history_dir / f"{metadata.name}.json"
        
        # If it exists, update the last_accessed_at, but preserve pinned status
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = RepositoryMetadata(**json.load(f))
                    # Merge properties if needed
                    pinned = existing.pinned
            except Exception:
                pinned = False
                
            # Create a new dict and parse it to preserve immutability
            d = metadata.model_dump()
            d["pinned"] = pinned
            d["last_accessed_at"] = datetime.now(timezone.utc).isoformat()
            metadata = RepositoryMetadata(**d)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))
            
    def get_repository(self, name: str) -> Optional[RepositoryMetadata]:
        file_path = self.history_dir / f"{name}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    meta = RepositoryMetadata(**json.load(f))
                    
                # Update last accessed
                d = meta.model_dump()
                d["last_accessed_at"] = datetime.now(timezone.utc).isoformat()
                meta = RepositoryMetadata(**d)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(meta.model_dump_json(indent=2))
                    
                return meta
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to load repository history for {name}: {e}")
        return None
        
    def list_repositories(self) -> List[RepositoryMetadata]:
        repos = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    repos.append(RepositoryMetadata(**json.load(f)))
            except Exception:
                continue
        
        # Sort pinned first, then by last accessed
        def _get_sort_key(x):
            dt = x.last_accessed_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (x.pinned, dt)
            
        repos.sort(key=_get_sort_key, reverse=True)
        return repos
        
    def pin_repository(self, name: str, pinned: bool) -> bool:
        meta = self.get_repository(name)
        if meta:
            d = meta.model_dump()
            d["pinned"] = pinned
            updated_meta = RepositoryMetadata(**d)
            with open(self.history_dir / f"{name}.json", "w", encoding="utf-8") as f:
                f.write(updated_meta.model_dump_json(indent=2))
            return True
        return False
        
    def delete_repository(self, name: str) -> bool:
        file_path = self.history_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            
            # Also clean up investigation caches
            from app.services.investigation_cache import CACHE_DIR as INV_CACHE_DIR
            for inv_file in INV_CACHE_DIR.glob(f"{name}_*.json"):
                inv_file.unlink()
                
            return True
        return False

    def search_repositories(self, query: str) -> List[RepositoryMetadata]:
        query = query.lower()
        repos = self.list_repositories()
        results = []
        for repo in repos:
            if query in repo.name.lower() or (repo.url and query in repo.url.lower()):
                results.append(repo)
            else:
                # Check tech stack
                found = False
                for cat, items in repo.tech_stack_summary.items():
                    for item in items:
                        if query in item.lower():
                            found = True
                            break
                    if found: break
                if found:
                    results.append(repo)
        return results
