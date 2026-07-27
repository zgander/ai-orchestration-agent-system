import re
import git
import shutil
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)

class InvalidURLError(Exception):
    pass

class CloneError(Exception):
    pass

class GitHubService:
    def __init__(self):
        self.url_pattern = re.compile(r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+/?$")

    def validate_url(self, url: str) -> bool:
        """Validate if the given string is a valid GitHub repository URL."""
        # Strip trailing .git if present
        if url.endswith(".git"):
            url = url[:-4]
        return bool(self.url_pattern.match(url))

    def clone(self, url: str, target_dir: Path) -> Path:
        """
        Clone a GitHub repository to the target directory.
        Only clones depth=1 to save time/bandwidth.
        """
        if not self.validate_url(url):
            raise InvalidURLError(f"Invalid GitHub URL: {url}")

        logger.info(f"Cloning {url} to {target_dir}")
        try:
            # We don't checkout submodules in Phase 1 to prevent arbitrary code execution / recursion issues
            git.Repo.clone_from(url, target_dir, depth=1)
            return target_dir
        except git.exc.GitCommandError as e:
            # Clean up partial clones
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            logger.error(f"Failed to clone repository: {e}")
            raise CloneError(f"Failed to clone repository: Ensure it is public and valid.") from e
        except Exception as e:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            logger.error(f"Unexpected error during clone: {e}")
            raise CloneError(f"Unexpected error during cloning: {e}") from e
