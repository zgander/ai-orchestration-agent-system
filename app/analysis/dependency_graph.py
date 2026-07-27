import ast
import re
import networkx as nx
from pathlib import Path
from typing import List, Dict, Optional

from app.models.analysis_models import DependencyEdge, DependencyGraphModel
from app.config.settings import Settings
from app.utils.file_utils import find_files, safe_read_text, get_file_extension


class DependencyGraph:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyse(self, root_path: Path) -> DependencyGraphModel:
        graph = nx.DiGraph()
        
        # Build mapping of file paths to their potential import names
        # E.g., app/models/repository.py -> app.models.repository
        file_map: Dict[str, str] = {}
        all_files = list(find_files(root_path, self.settings))
        
        for file_path in all_files:
            rel_path = str(file_path.relative_to(root_path)).replace('\\', '/')
            graph.add_node(rel_path)
            
            ext = get_file_extension(file_path)
            if ext == ".py":
                # Convert app/models/repository.py to app.models.repository
                module_path = rel_path.replace('/', '.').removesuffix('.py')
                if module_path.endswith('.__init__'):
                    module_path = module_path.removesuffix('.__init__')
                file_map[module_path] = rel_path
            elif ext in [".js", ".jsx", ".ts", ".tsx"]:
                # Convert src/components/Button.js to src/components/Button
                module_path = rel_path
                for suffix in [".js", ".jsx", ".ts", ".tsx"]:
                    module_path = module_path.removesuffix(suffix)
                file_map[module_path] = rel_path

        # Parse files to find edges
        for file_path in all_files:
            ext = get_file_extension(file_path)
            rel_path = str(file_path.relative_to(root_path)).replace('\\', '/')
            content = safe_read_text(file_path)
            
            if not content:
                continue

            if ext == ".py":
                self._analyse_python(content, rel_path, file_map, graph)
            elif ext in [".js", ".jsx", ".ts", ".tsx"]:
                self._analyse_javascript(content, rel_path, file_map, graph, root_path, file_path)

        edges: List[DependencyEdge] = []
        for source, target, data in graph.edges(data=True):
            edges.append(DependencyEdge(
                source_file=source,
                target_file=target,
                import_name=data.get('import_name', 'unknown')
            ))
            
        components = nx.number_weakly_connected_components(graph) if len(graph) > 0 else 0
        
        # Calculate most connected (in-degree + out-degree)
        degrees = dict(graph.degree())
        most_connected = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:5]
        
        return DependencyGraphModel(
            nodes=list(graph.nodes()),
            edges=edges,
            connected_components=components,
            most_connected=most_connected
        )

    def _analyse_python(self, content: str, source_rel_path: str, file_map: Dict[str, str], graph: nx.DiGraph):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Try to find the exact module or its parent in our project
                        target_path = self._resolve_python_import(alias.name, file_map)
                        if target_path:
                            graph.add_edge(source_rel_path, target_path, import_name=alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    # relative imports (level > 0) are trickier, but we can do a basic check
                    if node.level > 0:
                        # Very basic relative import handling for Phase 1
                        parts = source_rel_path.split('/')[:-node.level]
                        if node.module:
                            parts.append(node.module.replace('.', '/'))
                        full_module = '.'.join(parts)
                        target_path = self._resolve_python_import(full_module, file_map)
                    else:
                        target_path = self._resolve_python_import(node.module, file_map)
                        
                    if target_path:
                        for alias in node.names:
                            graph.add_edge(source_rel_path, target_path, import_name=alias.name)
        except SyntaxError:
            pass

    def _resolve_python_import(self, module_name: str, file_map: Dict[str, str]) -> Optional[str]:
        # Exact match
        if module_name in file_map:
            return file_map[module_name]
        
        # Package match (e.g., import `app.models`, resolves to `app/models/__init__.py`)
        if module_name in file_map: # Handled by exact match if __init__ logic is correct
            return file_map[module_name]
            
        # Maybe it's importing a function from a module, so the module name is the parent
        parts = module_name.split('.')
        while parts:
            partial_name = '.'.join(parts)
            if partial_name in file_map:
                return file_map[partial_name]
            parts.pop()
            
        return None

    def _analyse_javascript(self, content: str, source_rel_path: str, file_map: Dict[str, str], graph: nx.DiGraph, root_path: Path, file_path: Path):
        # Matches: import { x } from './utils', import X from '../api', require('./lib')
        import_pattern = r"(?:import.*from|require\s*\()\s*['\"]([^'\"]+)['\"]"
        
        for match in re.finditer(import_pattern, content):
            import_path = match.group(1)
            
            # We only care about internal imports (starting with . or /)
            # Aliases like @/components are harder without parsing tsconfig, so we skip for Phase 1 or try to guess.
            if import_path.startswith('.'):
                # Resolve relative path
                current_dir = file_path.parent
                try:
                    resolved_path = (current_dir / import_path).resolve()
                    # Check if it's within root
                    if root_path in resolved_path.parents:
                        rel_import = str(resolved_path.relative_to(root_path)).replace('\\', '/')
                        
                        # Find matching file in file_map
                        if rel_import in file_map:
                            graph.add_edge(source_rel_path, file_map[rel_import], import_name=import_path)
                        else:
                            # It might be a directory import (index.js)
                            index_rel = f"{rel_import}/index"
                            if index_rel in file_map:
                                graph.add_edge(source_rel_path, file_map[index_rel], import_name=import_path)
                except (ValueError, RuntimeError):
                    pass
