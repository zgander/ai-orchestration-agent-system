import streamlit as st
from app.services.repository_history import RepositoryHistoryService

def render_repo_history_page():
    st.title("📚 Repository History")
    st.write("Browse and manage your previously analysed repositories.")
    
    history_service = RepositoryHistoryService()
    
    search_query = st.text_input("🔍 Search repositories...", placeholder="Search by name, URL, or tech stack...")
    
    if search_query:
        repos = history_service.search_repositories(search_query)
    else:
        repos = history_service.list_repositories()
        
    if not repos:
        st.info("No repositories found in history.")
        return
        
    for repo in repos:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                pin_icon = "📌" if repo.pinned else "📍"
                st.markdown(f"### {pin_icon} {repo.name}")
                if repo.url:
                    st.caption(f"[{repo.url}]({repo.url})")
                    
                # Tech stack badges
                badges = []
                for cat, items in repo.tech_stack_summary.items():
                    for item in items[:3]:  # Show max 3 per category
                        badges.append(item)
                
                if badges:
                    st.markdown("`" + "` `".join(badges[:6]) + "`") # Show up to 6 badges
                    
            with col2:
                st.markdown("**Last Analysed:**")
                st.write(repo.analysed_at.strftime("%Y-%m-%d %H:%M"))
                st.markdown("**Status:**")
                st.write(repo.investigation_status.value)
                
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Load", key=f"load_{repo.name}", use_container_width=True):
                    # We need to reload analysis and investigation from cache
                    from app.services.repository_service import RepositoryService
                    from app.services.investigation_cache import load_investigation_result
                    
                    # Here we simulate loading from a saved state or cache
                    st.toast(f"Loading {repo.name} is not fully implemented for restoring AnalysisResult yet, but cache is ready.", icon="⚠️")
                    
                if st.button("Pin" if not repo.pinned else "Unpin", key=f"pin_{repo.name}", use_container_width=True):
                    history_service.pin_repository(repo.name, not repo.pinned)
                    st.rerun()
                    
                if st.button("Delete", key=f"del_{repo.name}", type="primary", use_container_width=True):
                    history_service.delete_repository(repo.name)
                    st.rerun()
