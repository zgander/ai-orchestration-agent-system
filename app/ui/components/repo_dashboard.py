import streamlit as st
import pandas as pd
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
    
    # Check if investigation is complete
    inv_result = st.session_state.get("investigation_result")
    
    if inv_result and inv_result.onboarding_guide:
        guide = inv_result.onboarding_guide
        st.markdown("## 🧠 AI Onboarding Mentor Insights")
        
        col_ment1, col_ment2 = st.columns(2)
        
        with col_ment1:
            st.markdown("### Mental Model")
            st.info(guide.mental_model)
            
            st.markdown("### Repository at a Glance")
            ro = guide.repository_overview
            glance_data = {
                "Project Type": ro.project_type,
                "Primary Purpose": ro.primary_purpose,
                "Complexity": ro.estimated_complexity,
                "Est. Learning Time": f"{ro.estimated_learning_time_minutes} mins"
            }
            st.table(pd.DataFrame(list(glance_data.items()), columns=["Metric", "Value"]))
            
        with col_ment2:
            st.markdown("### Starting Point")
            if guide.important_files:
                top_files = sorted(guide.important_files, key=lambda x: x.rank)[:3]
                for file in top_files:
                    st.write(f"- 📄 `{file.file_path}`: {file.purpose}")
            else:
                st.write("No specific files recommended.")
                
            if hasattr(guide, 'repository_health') and guide.repository_health:
                st.markdown("### Repository Health")
                for score in guide.repository_health:
                    icon = "✅" if score.score.lower() in ["good", "excellent", "high"] else "⚠️" if score.score.lower() in ["average", "medium", "fair"] else "❌"
                    st.write(f"{icon} **{score.category}**: {score.score}")
                    
        st.divider()
    else:
        # 2. Stats (pre-investigation)
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
        st.markdown("### 🤖 Investigation Actions")
        if not inv_result:
            st.write("Launch the Multi-Agent system to deeply understand this repository.")
        
        status_text = "Ready to start"
        if inv_result:
            status_text = "Completed"
            
        st.info(f"Status: **{status_text}**")
        
        btn_text = "🔍 View Full Investigation Guide" if inv_result else "🚀 Start AI Investigation"
        if st.button(btn_text, type="primary", use_container_width=True):
            st.session_state.app_state = "investigation"
            st.rerun()
            
    with col_action2:
        st.markdown("### 💬 Ask Questions")
        st.write("Already have an idea? Ask the assistant directly.")
        
        if not inv_result:
            st.warning("Chat works best after an AI investigation.")
            
        if st.button("💬 Open Chat Assistant", use_container_width=True):
            st.session_state.app_state = "chat"
            st.rerun()
