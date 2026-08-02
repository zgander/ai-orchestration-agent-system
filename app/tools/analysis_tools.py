import json
from pathlib import Path
from langchain_core.tools import tool

from app.analysis.dependency_graph import DependencyGraph
from app.analysis.symbol_index import SymbolIndexBuilder
from app.config.settings import Settings

# We import the global cache from repository_tools to share it across the session
from app.tools.repository_tools import _TOOL_CACHE

from app.tools.tool_context import get_root_path



@tool
def search_symbols(query: str) -> str:
    """
    Searches for a specific class, function, or method by name in the code.
    Use this to find the definition of a specific symbol.
    """
    root_path = get_root_path()
    cache_key = ("symbol_index", root_path)
    if cache_key not in _TOOL_CACHE:
        builder = SymbolIndexBuilder(Settings())
        index = builder.analyse(Path(root_path))
        _TOOL_CACHE[cache_key] = index
    else:
        index = _TOOL_CACHE[cache_key]
        
    results = index.lookup(query)
    
    if not results:
        return f"No symbols found matching '{query}'"
        
    summary = [
        {"name": s.name, "kind": s.kind.value, "file": s.file_path, "line": s.line_number, "parent": s.parent_class}
        for s in results
    ]
    
    return json.dumps(summary, indent=2)

@tool
def get_file_dependencies(file_path: str) -> str:
    """
    Returns the files that the target file imports, and the files that import the target file.
    Use this to understand the relationships and dependencies of a specific file.
    file_path should be relative to the repository root.
    """
    root_path = get_root_path()
    
    # Build or use hidden cache for the full dependency graph model
    full_graph_cache_key = ("dependency_graph_full", root_path)
    if full_graph_cache_key not in _TOOL_CACHE:
        builder = DependencyGraph(Settings())
        graph = builder.analyse(Path(root_path))
        _TOOL_CACHE[full_graph_cache_key] = graph
    else:
        graph = _TOOL_CACHE[full_graph_cache_key]
        
    # Find incoming and outgoing edges for file_path
    imports = []
    imported_by = []
    
    # Convert backslashes just in case
    file_path = file_path.replace('\\', '/')
    
    for edge in graph.edges:
        if edge.source_file == file_path:
            imports.append({"file": edge.target_file, "import": edge.import_name})
        elif edge.target_file == file_path:
            imported_by.append({"file": edge.source_file, "import": edge.import_name})
            
    summary = {
        "file": file_path,
        "imports": imports,
        "imported_by": imported_by
    }
    
    return json.dumps(summary, indent=2)
