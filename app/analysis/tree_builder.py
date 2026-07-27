import os
from pathlib import Path
from app.models.analysis_models import FileNode, RepositoryTree
from app.config.settings import Settings
from app.utils.file_utils import is_ignored
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TreeBuilder:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.total_files = 0
        self.total_dirs = 0
        self.max_depth = 0

    def analyse(self, root_path: Path) -> RepositoryTree:
        self.total_files = 0
        self.total_dirs = 0
        self.max_depth = 0
        
        root_node = self._build_tree(root_path, depth=0)
        
        return RepositoryTree(
            root=root_node,
            total_files=self.total_files,
            total_dirs=self.total_dirs,
            max_depth=self.max_depth
        )

    def _build_tree(self, current_path: Path, depth: int) -> FileNode:
        if depth > self.max_depth:
            self.max_depth = depth

        is_dir = current_path.is_dir()
        size = 0
        children = []

        if not is_dir:
            try:
                size = current_path.stat().st_size
                self.total_files += 1
            except OSError:
                size = 0
        else:
            self.total_dirs += 1
            try:
                with os.scandir(current_path) as it:
                    for entry in it:
                        entry_path = Path(entry.path)
                        if not is_ignored(entry_path, self.settings):
                            child_node = self._build_tree(entry_path, depth + 1)
                            children.append(child_node)
                            size += child_node.size
            except PermissionError:
                logger.warning(f"Permission denied: {current_path}")
            except OSError as e:
                logger.warning(f"Error reading directory {current_path}: {e}")

        # Sort children: directories first, then alphabetically
        children.sort(key=lambda x: (not x.is_dir, x.name.lower()))

        return FileNode(
            name=current_path.name,
            path=str(current_path),
            is_dir=is_dir,
            size=size,
            depth=depth,
            children=children
        )
