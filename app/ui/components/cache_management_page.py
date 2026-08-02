import streamlit as st
import os
import shutil
from pathlib import Path

from app.services.investigation_cache import CACHE_DIR

def render_cache_management_page():
    st.title("🗄️ Cache Management")
    st.write("Manage stored investigation results, analysis data, and chat sessions to free up disk space.")
    
    col1, col2, col3 = st.columns(3)
    
    inv_cache_size = _get_dir_size(CACHE_DIR) if CACHE_DIR.exists() else 0
    chat_cache_dir = Path(".repolens_cache/chat_sessions")
    chat_cache_size = _get_dir_size(chat_cache_dir) if chat_cache_dir.exists() else 0
    history_dir = Path(".repolens_cache/repository_history")
    history_size = _get_dir_size(history_dir) if history_dir.exists() else 0
    
    total_size = inv_cache_size + chat_cache_size + history_size
    
    with col1:
        st.metric("Total Cache Size", f"{total_size / (1024*1024):.2f} MB")
    with col2:
        st.metric("Investigations", f"{inv_cache_size / (1024*1024):.2f} MB")
    with col3:
        st.metric("Chat History", f"{chat_cache_size / (1024*1024):.2f} MB")
        
    st.divider()
    
    st.subheader("Investigation Cache")
    if CACHE_DIR.exists() and any(CACHE_DIR.iterdir()):
        for file_path in CACHE_DIR.glob("*.json"):
            col_name, col_size, col_action = st.columns([3, 1, 1])
            with col_name:
                st.write(file_path.name)
            with col_size:
                st.write(f"{file_path.stat().st_size / 1024:.1f} KB")
            with col_action:
                if st.button("Delete", key=f"del_inv_{file_path.name}", type="primary"):
                    file_path.unlink()
                    st.rerun()
    else:
        st.write("Investigation cache is empty.")
        
    st.divider()
    
    st.subheader("Chat Sessions")
    if chat_cache_dir.exists() and any(chat_cache_dir.iterdir()):
        for repo_dir in chat_cache_dir.iterdir():
            if repo_dir.is_dir():
                with st.expander(f"📁 {repo_dir.name} ({_get_dir_size(repo_dir) / 1024:.1f} KB)"):
                    for session_file in repo_dir.glob("*.json"):
                        col_sn, col_sz, col_sa = st.columns([3, 1, 1])
                        with col_sn:
                            st.write(session_file.name)
                        with col_sz:
                            st.write(f"{session_file.stat().st_size / 1024:.1f} KB")
                        with col_sa:
                            if st.button("Delete", key=f"del_chat_{session_file.name}"):
                                session_file.unlink()
                                st.rerun()
    else:
        st.write("Chat cache is empty.")
        
    st.divider()
    
    st.warning("Danger Zone")
    if st.button("Clear All Caches (Irreversible)"):
        if CACHE_DIR.exists(): shutil.rmtree(CACHE_DIR)
        if chat_cache_dir.exists(): shutil.rmtree(chat_cache_dir)
        # We don't delete history_dir here to preserve the list
        st.success("Caches cleared successfully!")
        st.rerun()

def _get_dir_size(path: Path) -> int:
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size
