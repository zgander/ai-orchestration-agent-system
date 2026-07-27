import os
import json
from pathlib import Path
from langchain_core.tools import tool

from app.analysis.tree_builder import TreeBuilder
from app.config.settings import Settings
from app.utils.file_utils import safe_read_text, find_files

# Global cache for expensive tool calls per investigation session
_TOOL_CACHE = {}

def clear_tool_cache():
    global _TOOL_CACHE
    _TOOL_CACHE.clear()

from app.tools.tool_context import get_root_path

@tool
def get_repository_tree() -> str:
    """
    Returns a summary of the repository directory structure.
    Use this to understand the high-level layout of the project, important folders, and where source code lives.
    """
    root_path = get_root_path()
    cache_key = ("tree", root_path)
    if cache_key in _TOOL_CACHE:
        return _TOOL_CACHE[cache_key]

    builder = TreeBuilder(Settings())
    tree = builder.analyse(Path(root_path))
    
    # We serialize just the top levels to avoid blowing up context window
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
        
    summary = {
        "total_files": tree.total_files,
        "total_dirs": tree.total_dirs,
        "max_depth": tree.max_depth,
        "root": _node_to_dict(tree.root)
    }
    
    res = json.dumps(summary, indent=2)
    _TOOL_CACHE[cache_key] = res
    return res

@tool
def read_file(file_path: str) -> str:
    """
    Reads the content of a file.
    Use this to inspect specific code files, configuration files, or documentation.
    file_path should be relative to the repository root.
    """
    root_path = get_root_path()
    root = Path(root_path).resolve()
    target = (root / file_path).resolve()
    
    if not str(target).startswith(str(root)):
        return "Error: Cannot read files outside the repository root."
        
    if not target.exists() or not target.is_file():
        return f"Error: File '{file_path}' does not exist or is not a file."
        
    content = safe_read_text(target)
    if content is None:
        return f"Error: Could not read file '{file_path}'. It may be binary or use an unsupported encoding."
        
    # Truncate if too long (e.g. 500 lines)
    lines = content.split('\n')
    max_lines = 500
    if len(lines) > max_lines:
        content = '\n'.join(lines[:max_lines]) + f"\n... (File truncated, {len(lines) - max_lines} lines omitted)"
        
    return content

@tool
def search_files(pattern: str) -> str:
    """
    Searches for files containing a specific regex pattern.
    Use this to find specific keywords, function calls, or configurations across the repository.
    """
    import re
    
    try:
        regex = re.compile(pattern)
    except re.error:
        return f"Error: Invalid regex pattern '{pattern}'"
        
    results = []
    root_path = get_root_path()
    root = Path(root_path)
    
    for file_path in find_files(root, Settings()):
        content = safe_read_text(file_path)
        if content:
            matches = list(regex.finditer(content))
            if matches:
                rel_path = str(file_path.relative_to(root)).replace('\\', '/')
                # Get the first match context
                match = matches[0]
                line_no = content[:match.start()].count('\n') + 1
                line_start = max(0, content.rfind('\n', 0, match.start()) + 1)
                line_end = content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(content)
                snippet = content[line_start:line_end].strip()
                
                results.append({
                    "file": rel_path,
                    "matches": len(matches),
                    "example": f"Line {line_no}: {snippet}"
                })
                
                if len(results) >= 20:
                    break
                    
    if not results:
        return f"No matches found for pattern '{pattern}'"
        
    if len(results) == 20:
        results.append({"note": "Search results truncated to 20 files."})
        
    return json.dumps(results, indent=2)

@tool
def list_directory(dir_path: str) -> str:
    """
    Lists the contents of a specific directory.
    Use this to see what files and folders are inside a specific directory.
    dir_path should be relative to the repository root. Use '.' for the root directory.
    """
    root_path = get_root_path()
    root = Path(root_path).resolve()
    target = (root / dir_path).resolve()
    
    if not str(target).startswith(str(root)):
        return "Error: Cannot access directories outside the repository root."
        
    if not target.exists() or not target.is_dir():
        return f"Error: Directory '{dir_path}' does not exist or is not a directory."
        
    contents = []
    for item in target.iterdir():
        contents.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else 0
        })
        
    return json.dumps(contents, indent=2)
