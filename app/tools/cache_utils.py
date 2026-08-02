import json
from app.models.analysis_models import AnalysisResult
from app.tools.repository_tools import _TOOL_CACHE, _CACHE_LOCK

def preseed_tool_cache(analysis_result: AnalysisResult):
    """
    Populates the global tool cache with results from Phase 1.
    This prevents agents from re-running expensive analysis operations.
    """
    root_path = analysis_result.repository_info.root_path
    
    # 1. Tech Stack
    tech_stack_summary = {
        "languages": [{"name": i.name, "confidence": i.confidence} for i in analysis_result.tech_stack.languages],
        "frameworks": [{"name": i.name, "confidence": i.confidence} for i in analysis_result.tech_stack.frameworks],
        "databases": [{"name": i.name, "confidence": i.confidence} for i in analysis_result.tech_stack.databases],
        "others": [{"name": i.name, "category": i.category.value, "confidence": i.confidence} 
                  for i in analysis_result.tech_stack.items if i.category.value not in ["LANGUAGE", "FRAMEWORK", "DATABASE"]]
    }
    
    # 2. Dependency Graph
    deps_summary = {
        "total_nodes": len(analysis_result.dependency_graph.nodes),
        "total_edges": len(analysis_result.dependency_graph.edges),
        "connected_components": analysis_result.dependency_graph.connected_components,
        "most_connected_files": analysis_result.dependency_graph.most_connected
    }
    
    # 3. Entry Points
    entry_summary = [
        {"file": e.file_path, "line": e.line_number, "description": e.description, "confidence": e.confidence}
        for e in analysis_result.entry_points
    ]
    
    # 4. API Endpoints
    api_summary = [
        {"method": e.method, "path": e.path, "framework": e.framework, "handler": e.handler_name, "file": e.file_path}
        for e in analysis_result.api_endpoints
    ]
    
    # 5. Environment Variables
    unique_names = list(set(e.name for e in analysis_result.env_variables))
    env_summary = {"variables": sorted(unique_names)}
    
    # 6. Symbol Index (Not JSON dumped since it's an object)
    
    # 7. Tree
    def _node_to_dict(node, max_depth=3):
        if node.depth > max_depth:
            return {"name": node.name, "is_dir": node.is_dir, "omitted": True}
        result = {
            "name": node.name,
            "is_dir": node.is_dir,
            "size": node.size
        }
        if node.is_dir and node.children:
            result["children"] = [_node_to_dict(c, max_depth) for c in node.children]
        return result
        
    tree_summary = {
        "total_files": analysis_result.tree.total_files,
        "total_dirs": analysis_result.tree.total_dirs,
        "max_depth": analysis_result.tree.max_depth,
        "root": _node_to_dict(analysis_result.tree.root)
    }

    # Safely write to cache
    with _CACHE_LOCK:
        _TOOL_CACHE[("tech_stack", root_path)] = json.dumps(tech_stack_summary, indent=2)
        _TOOL_CACHE[("dependency_graph", root_path)] = json.dumps(deps_summary, indent=2)
        _TOOL_CACHE[("dependency_graph_full", root_path)] = analysis_result.dependency_graph
        _TOOL_CACHE[("entry_points", root_path)] = json.dumps(entry_summary, indent=2)
        _TOOL_CACHE[("api_endpoints", root_path)] = json.dumps(api_summary, indent=2)
        _TOOL_CACHE[("env_variables", root_path)] = json.dumps(env_summary, indent=2)
        _TOOL_CACHE[("symbol_index", root_path)] = analysis_result.symbol_index
        _TOOL_CACHE[("tree", root_path)] = json.dumps(tree_summary, indent=2)
