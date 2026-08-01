import streamlit as st
import os
from app.tools.repository_tools import read_file
from app.tools.tool_context import get_root_path

def render_code_viewer(file_path: str):
    st.markdown(f"### 📄 Code Viewer: `{file_path}`")
    try:
        # Assuming the tool gives us string back directly
        content = read_file.invoke({"file_path": file_path})
        
        # Determine language for syntax highlighting
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".json": "json",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".sh": "bash"
        }
        lang = language_map.get(ext, "text")
        
        st.code(content, language=lang)
    except Exception as e:
        st.error(f"Could not load file: {e}")
        
    if st.button("Close Viewer"):
        st.session_state.active_code_viewer = None
        st.rerun()
