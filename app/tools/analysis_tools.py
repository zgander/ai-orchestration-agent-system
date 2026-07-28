import json
from pathlib import Path
from langchain_core.tools import tool

from app.analysis.stack_detector import StackDetector
from app.analysis.dependency_graph import DependencyGraph
from app.analysis.entry_detector import EntryDetector
from app.analysis.api_detector import APIDetector
from app.analysis.env_detector import EnvDetector
from app.analysis.symbol_index import SymbolIndexBuilder
from app.config.settings import Settings

# We import the global cache from repository_tools to share it across the session
from app.tools.repository_tools import _TOOL_CACHE

from app.tools.tool_context import get_root_path

@tool
def get_tech_stack() -> str:
    """
    Returns the detected technology stack of the repository.
    Use this to identify programming languages, frameworks, databases, package managers, and CI/CD tools.
    """
    root_path = get_root_path()
    cache_key = ("tech_stack", root_path)
    if cache_key in _TOOL_CACHE:
        return _TOOL_CACHE[cache_key]

    detector = StackDetector(Settings())
    stack = detector.analyse(Path(root_path))
    
    summary = {
        "languages": [{"name": i.name, "confidence": i.confidence} for i in stack.languages],
        "frameworks": [{"name": i.name, "confidence": i.confidence} for i in stack.frameworks],
        "databases": [{"name": i.name, "confidence": i.confidence} for i in stack.databases],
        "others": [{"name": i.name, "category": i.category.value, "confidence": i.confidence} 
                  for i in stack.items if i.category.value not in ["LANGUAGE", "FRAMEWORK", "DATABASE"]]
    }
    
    res = json.dumps(summary, indent=2)
    _TOOL_CACHE[cache_key] = res
    return res

@tool
def get_dependency_graph() -> str:
    """
    Returns a summary of the repository's dependency graph.
    Use this to identify highly connected "hub" files and the overall modularity (connected components).
    """
    root_path = get_root_path()
    cache_key = ("dependency_graph", root_path)
    if cache_key in _TOOL_CACHE:
        return _TOOL_CACHE[cache_key]

    builder = DependencyGraph(Settings())
    graph = builder.analyse(Path(root_path))
    
    summary = {
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges),
        "connected_components": graph.connected_components,
        "most_connected_files": graph.most_connected
    }
    
    res = json.dumps(summary, indent=2)
    _TOOL_CACHE[cache_key] = res
    return res

@tool
def get_entry_points() -> str:
    """
    Returns the detected entry points of the application (e.g. main.py, server.js).
    Use this to find where the application starts execution.
    """
    root_path = get_root_path()
    cache_key = ("entry_points", root_path)
    if cache_key in _TOOL_CACHE:
        return _TOOL_CACHE[cache_key]

    detector = EntryDetector(Settings())
    entries = detector.analyse(Path(root_path))
    
    summary = [
        {"file": e.file_path, "line": e.line_number, "description": e.description, "confidence": e.confidence}
        for e in entries
    ]
    
    res = json.dumps(summary, indent=2)
    _TOOL_CACHE[cache_key] = res
    return res

@tool
def get_api_endpoints() -> str:
    """
    Returns the detected API endpoints in the repository.
    Use this to understand the API surface, routes, and controllers.
    """
    root_path = get_root_path()
    cache_key = ("api_endpoints", root_path)
    if cache_key in _TOOL_CACHE:
        return _TOOL_CACHE[cache_key]

    detector = APIDetector(Settings())
    endpoints = detector.analyse(Path(root_path))
    
    summary = [
        {"method": e.method, "path": e.path, "framework": e.framework, "handler": e.handler_name, "file": e.file_path}
        for e in endpoints
    ]
    
    res = json.dumps(summary, indent=2)
    _TOOL_CACHE[cache_key] = res
    return res

@tool
def get_environment_variables() -> str:
    """
    Returns the detected environment variables required by the application.
    Use this to understand configuration requirements.
    """
    root_path = get_root_path()
    cache_key = ("env_variables", root_path)
    if cache_key in _TOOL_CACHE:
        return _TOOL_CACHE[cache_key]

    detector = EnvDetector(Settings())
    envs = detector.analyse(Path(root_path))
    
    # Deduplicate by name
    unique_names = list(set(e.name for e in envs))
    
    summary = {"variables": sorted(unique_names)}
    
    res = json.dumps(summary, indent=2)
    _TOOL_CACHE[cache_key] = res
    return res

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
