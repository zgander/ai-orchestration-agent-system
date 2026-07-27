import time
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import shutil

from app.models.repository import RepositoryInfo, RepositorySource, SourceType
from app.models.analysis_models import AnalysisResult, RepositoryStatistics
from app.config.settings import Settings
from app.utils.logger import get_logger, time_it

from app.services.github_service import GitHubService
from app.services.zip_service import ZipService

from app.analysis.tree_builder import TreeBuilder
from app.analysis.stack_detector import StackDetector
from app.analysis.entry_detector import EntryDetector
from app.analysis.api_detector import APIDetector
from app.analysis.env_detector import EnvDetector
from app.analysis.dependency_graph import DependencyGraph
from app.analysis.symbol_index import SymbolIndexBuilder

logger = get_logger(__name__)

class RepositoryTooLargeError(Exception):
    pass

class RepositoryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.github_service = GitHubService()
        self.zip_service = ZipService()
        
        # Analysers
        self.tree_builder = TreeBuilder(settings)
        self.stack_detector = StackDetector(settings)
        self.entry_detector = EntryDetector(settings)
        self.api_detector = APIDetector(settings)
        self.env_detector = EnvDetector(settings)
        self.dependency_graph = DependencyGraph(settings)
        self.symbol_index = SymbolIndexBuilder(settings)

    def ingest(self, source_type: SourceType, url_or_file, target_dir: Path) -> RepositoryInfo:
        """
        Ingest the repository either from GitHub or a ZIP file.
        Returns RepositoryInfo.
        """
        root_path = target_dir
        url = None
        
        if source_type == SourceType.GITHUB:
            url = url_or_file
            root_path = self.github_service.clone(url, target_dir)
            name = url.rstrip('/').split('/')[-1]
            if name.endswith('.git'):
                name = name[:-4]
        elif source_type == SourceType.ZIP:
            # url_or_file is a Path or file-like object
            root_path = self.zip_service.extract(url_or_file, target_dir)
            name = Path(url_or_file).stem
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        # Check size limits
        size_bytes = sum(f.stat().st_size for f in root_path.rglob('*') if f.is_file())
        if size_bytes > self.settings.max_repo_size_mb * 1024 * 1024:
            raise RepositoryTooLargeError(f"Repository exceeds {self.settings.max_repo_size_mb}MB limit.")

        source = RepositorySource(
            source_type=source_type,
            url=url,
            local_path=str(root_path)
        )

        return RepositoryInfo(
            name=name,
            source=source,
            root_path=str(root_path),
            cloned_at=datetime.now(timezone.utc),
            size_bytes=size_bytes
        )

    def analyse(self, repo_info: RepositoryInfo) -> AnalysisResult:
        """
        Run all analysis modules on the ingested repository.
        """
        root_path = Path(repo_info.root_path)
        start_time = time.time()
        
        logger.info(f"Starting analysis for {repo_info.name}")

        with time_it(logger, "Tree Builder"):
            tree = self.tree_builder.analyse(root_path)
            
        with time_it(logger, "Stack Detector"):
            tech_stack = self.stack_detector.analyse(root_path)
            
        with time_it(logger, "Entry Detector"):
            entry_points = self.entry_detector.analyse(root_path)
            
        with time_it(logger, "API Detector"):
            api_endpoints = self.api_detector.analyse(root_path)
            
        with time_it(logger, "Env Detector"):
            env_vars = self.env_detector.analyse(root_path)
            
        with time_it(logger, "Dependency Graph"):
            deps = self.dependency_graph.analyse(root_path)
            
        with time_it(logger, "Symbol Index"):
            symbols = self.symbol_index.analyse(root_path)

        duration = time.time() - start_time
        logger.info(f"Analysis completed in {duration:.2f} seconds")

        # Compile statistics
        lang_breakdown = {}
        for lang in tech_stack.languages:
            lang_breakdown[lang.name] = len(lang.evidence_files) # Approximation based on collected evidence (capped at 5 in detector)
            # Alternatively, recount. Let's just use what we have or add it to tree builder.
            # Actually stack_detector uses frequency but doesn't return full count. We'll leave it as is.
            
        # For largest dirs, just get top level from tree
        largest_dirs = {child.name: child.size for child in tree.root.children if child.is_dir}
        # Sort top 5
        largest_dirs = dict(sorted(largest_dirs.items(), key=lambda item: item[1], reverse=True)[:5])

        stats = RepositoryStatistics(
            total_files=tree.total_files,
            total_dirs=tree.total_dirs,
            total_source_files=sum(len(l.evidence_files) for l in tech_stack.languages), # Approximated
            languages_breakdown=lang_breakdown,
            largest_dirs=largest_dirs
        )

        return AnalysisResult(
            repository_info=repo_info,
            tree=tree,
            tech_stack=tech_stack,
            entry_points=entry_points,
            api_endpoints=api_endpoints,
            env_variables=env_vars,
            dependency_graph=deps,
            symbol_index=symbols,
            statistics=stats,
            analysed_at=datetime.now(timezone.utc),
            duration_seconds=duration
        )

    def cleanup(self, path: Path):
        """Clean up the temporary directory."""
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            logger.info(f"Cleaned up {path}")
