import json
from app.models.investigation_models import AgentType

def build_condensed_context(analysis_result_json: str, agent_type: AgentType) -> str:
    """
    Trims the massive analysis_result_json into a smaller dictionary 
    relevant to the specific agent type to save tokens.
    """
    try:
        data = json.loads(analysis_result_json)
    except json.JSONDecodeError:
        return analysis_result_json
        
    stats = data.get("statistics", {})
    repo = data.get("repository_info", {})
    tech = data.get("tech_stack", {})
    tree = data.get("tree", {})
    deps = data.get("dependency_graph", {})
    entry = data.get("entry_points", [])
    api = data.get("api_endpoints", [])
    env = data.get("env_variables", [])
    symbols = data.get("symbol_index", {})

    # Always provide these
    base = {
        "repository_name": repo.get("name"),
        "tech_stack_summary": tech
    }

    if agent_type == AgentType.ARCHITECTURE:
        # Needs tree (shallow), dep graph stats
        # Let's prune the tree heavily
        def prune_tree(node, depth=2):
            if not node: return node
            if node.get("depth", 0) > depth:
                return {"name": node.get("name"), "omitted": True}
            children = node.get("children", [])
            return {
                "name": node.get("name"),
                "is_dir": node.get("is_dir"),
                "children": [prune_tree(c, depth) for c in children] if children else []
            }
        base["tree_root"] = prune_tree(tree.get("root", {}))
        base["dependency_stats"] = {
            "total_nodes": deps.get("total_nodes"),
            "total_edges": deps.get("total_edges"),
            "connected_components": deps.get("connected_components")
        }
        
    elif agent_type == AgentType.EXECUTION_FLOW:
        # Needs entry points and basic dep edges
        base["entry_points"] = entry
        base["dependency_edges"] = deps.get("edges", [])
        
    elif agent_type == AgentType.API_DATA:
        # Needs API endpoints and symbol index
        base["api_endpoints"] = api
        base["symbols"] = symbols.get("symbols", [])
        base["dependency_edges"] = deps.get("edges", [])
        
    elif agent_type == AgentType.SETUP:
        # Needs env vars, entry points, testing tools
        base["env_variables"] = env
        base["entry_points"] = entry
        base["tech_stack_summary"] = tech
        
    else:
        # Fallback to everything
        return analysis_result_json

    return json.dumps(base, indent=2)
