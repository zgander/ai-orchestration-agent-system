import streamlit as st
from app.models.analysis_models import AnalysisResult
from app.ui.components.ui_helpers import render_metric_card

def render_repo_dashboard(analysis_result: AnalysisResult):
    st.title(f"📦 Repository: {analysis_result.repository_info.name}")
    
    # 1. Tech Stack Badges
    st.markdown("### Technologies Detected")
    badges = []
    for l in analysis_result.tech_stack.languages:
        badges.append(f'<span class="tech-badge badge-language">{l.name}</span>')
    for f in analysis_result.tech_stack.frameworks:
        badges.append(f'<span class="tech-badge badge-framework">{f.name}</span>')
    for d in analysis_result.tech_stack.databases:
        badges.append(f'<span class="tech-badge badge-database">{d.name}</span>')
    
    if badges:
        st.markdown(" ".join(badges), unsafe_allow_html=True)
    else:
        st.write("No specific technologies detected.")
        
    st.divider()
    
    # 2. Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Files", str(analysis_result.statistics.total_files), icon="📄")
    with col2:
        render_metric_card("Size (MB)", f"{analysis_result.repository_info.size_bytes / (1024*1024):.2f}", icon="💾")
    with col3:
        api_count = len(analysis_result.api_endpoints) if analysis_result.api_endpoints else 0
        render_metric_card("APIs", str(api_count), icon="🌐")
    with col4:
        ep_count = len(analysis_result.entry_points) if analysis_result.entry_points else 0
        render_metric_card("Entry Points", str(ep_count), icon="🚪")
        
    st.divider()
    
    # 3. Next Steps / Actions
    col_action1, col_action2 = st.columns(2)
    
    with col_action1:
        st.markdown("### 🤖 Ready for Investigation")
        st.write("Launch the Multi-Agent system to deeply understand this repository.")
        
        status_text = "Ready to start"
        if "investigation_result" in st.session_state:
            status_text = "Completed"
            
        st.info(f"Status: **{status_text}**")
        
        btn_text = "🔍 View Investigation Results" if "investigation_result" in st.session_state else "🚀 Start AI Investigation"
        if st.button(btn_text, type="primary", use_container_width=True):
            st.session_state.app_state = "investigation"
            st.rerun()
            
    with col_action2:
        st.markdown("### 💬 Ask Questions")
        st.write("Already have an idea? Ask the assistant directly.")
        
        if "investigation_result" not in st.session_state:
            st.warning("Chat works best after an AI investigation.")
            
        if st.button("💬 Open Chat Assistant", use_container_width=True):
            st.session_state.app_state = "chat"
            st.rerun()
