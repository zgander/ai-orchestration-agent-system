# Optional tools for chat agent if using a ReAct graph instead of simple LLM call
# Phase 4 currently uses direct LLM call without tools for the ChatAgent
# but this file is kept for future expansion (e.g. read_file access).
from langchain_core.tools import tool

@tool
def dummy_knowledge_tool(query: str) -> str:
    """Dummy tool for chat agent."""
    return f"Result for {query}"
