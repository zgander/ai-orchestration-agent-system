import streamlit as st
from typing import List
from app.models.analysis_models import FileNode

def render_tree(node: FileNode, level: int = 0):
    indent = "&nbsp;" * (level * 4)
    icon = "📁" if node.is_dir else "📄"
    
    html = f'<div class="tree-node">{indent}<span class="tree-icon">{icon}</span>{node.name}'
    if not node.is_dir:
        # format size nicely
        if node.size < 1024:
            size_str = f"{node.size} B"
        elif node.size < 1024 * 1024:
            size_str = f"{node.size / 1024:.1f} KB"
        else:
            size_str = f"{node.size / (1024*1024):.1f} MB"
        html += f' <span style="color: #9ca3af; font-size: 0.8em;">({size_str})</span>'
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    if node.is_dir and node.children:
        # To avoid massive trees lagging the UI in Phase 1, we cap depth or use expanders at top levels
        # Streamlit doesn't have a native tree view yet.
        for child in node.children:
            render_tree(child, level + 1)

def render_repository_tree(root: FileNode):
    st.markdown("### Repository Structure")
    
    # We will use expanders for top-level directories to make it manageable
    for child in root.children:
        if child.is_dir:
            with st.expander(f"📁 {child.name}"):
                for subchild in child.children:
                    render_tree(subchild, 1)
        else:
            render_tree(child, 0)
