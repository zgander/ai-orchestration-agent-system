import streamlit as st
import tempfile
from pathlib import Path
import os
import shutil

from app.models.repository import SourceType, UserRole, UserContext
from app.services.repository_service import RepositoryService
from app.config.settings import settings

def render_landing(repo_service: RepositoryService):
    st.markdown('<h1 class="hero-title">RepoLens</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">AI-Powered Multi-Agent Codebase Onboarding Assistant</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("1. Select Repository Source")
        source_mode = st.radio("Source", ["GitHub URL", "ZIP Upload"], horizontal=True, label_visibility="collapsed")
        
        url_input = None
        uploaded_file = None
        
        if source_mode == "GitHub URL":
            url_input = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repo")
        else:
            uploaded_file = st.file_uploader("Upload Repository ZIP", type=["zip"])
            
    with col2:
        st.subheader("2. Your Context")
        role = st.selectbox("Your Role", [r.value for r in UserRole])
        question = st.text_area("What are you looking for? (Optional)", placeholder="e.g. How does authentication work?")
        
    st.markdown("---")
    
    if st.button("🔍 Analyse Repository", use_container_width=True, type="primary"):
        if source_mode == "GitHub URL" and not url_input:
            st.error("Please enter a GitHub URL.")
            return
        if source_mode == "ZIP Upload" and not uploaded_file:
            st.error("Please upload a ZIP file.")
            return
            
        with st.status("Analysing Repository...", expanded=True) as status:
            temp_dir = Path(tempfile.mkdtemp(prefix="repolens_"))
            st.session_state['temp_dir'] = temp_dir
            
            try:
                # 1. Ingest
                st.write("📥 Ingesting repository...")
                if source_mode == "GitHub URL":
                    repo_info = repo_service.ingest(SourceType.GITHUB, url_input, temp_dir)
                else:
                    # Save uploaded file to temp
                    zip_path = temp_dir / uploaded_file.name
                    with open(zip_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    extract_dir = temp_dir / "extracted"
                    extract_dir.mkdir()
                    repo_info = repo_service.ingest(SourceType.ZIP, zip_path, extract_dir)
                    
                # 2. Analyse
                st.write(f"🔬 Analysing {repo_info.name}...")
                analysis_result = repo_service.analyse(repo_info)
                
                # Save context
                user_context = UserContext(
                    role=UserRole(role),
                    question=question if question else None
                )
                st.session_state['user_context'] = user_context
                st.session_state['analysis_result'] = analysis_result
                st.session_state['app_state'] = 'dashboard'
                
                status.update(label="Analysis Complete!", state="complete", expanded=False)
                st.rerun()
                
            except Exception as e:
                status.update(label="Analysis Failed", state="error")
                st.error(f"Error during analysis: {str(e)}")
                # Cleanup on failure
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
