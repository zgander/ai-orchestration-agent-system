import json
from app.models.analysis_models import AnalysisResult
from app.tools.repository_tools import _TOOL_CACHE, _CACHE_LOCK

def preseed_tool_cache(analysis_result: AnalysisResult):
    """
    Populates the global tool cache with results from Phase 1.
    This prevents agents from re-running expensive analysis operations for targeted tools
    like get_file_dependencies and search_symbols.
    """
    root_path = analysis_result.repository_info.root_path
    
    # Safely write to cache
    with _CACHE_LOCK:
        _TOOL_CACHE[("dependency_graph_full", root_path)] = analysis_result.dependency_graph
        _TOOL_CACHE[("symbol_index", root_path)] = analysis_result.symbol_index
