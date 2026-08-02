import streamlit as st
import sys
from pathlib import Path

# Add project root to path for imports
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.services.repository_service import RepositoryService
from app.config.settings import settings
from app.ui.components.landing import render_landing
from app.ui.components.dashboard import render_dashboard
from app.ui.components.investigation_dashboard import render_investigation_dashboard
from app.ui.components.onboarding_guide import render_onboarding_guide
from app.ui.components.reviewer_dashboard import render_reviewer_dashboard
from app.ui.components.chat_page import render_chat_page
from app.ui.components.repo_dashboard import render_repo_dashboard
from app.ui.components.repo_history_page import render_repo_history_page
from app.ui.components.settings_page import render_settings_page
from app.ui.components.analytics_page import render_analytics_page
from app.ui.components.monitoring_page import render_monitoring_page
from app.ui.components.cache_management_page import render_cache_management_page
from app.ui.components.performance_page import render_performance_page
from app.ui.components.dep_graph_page import render_dep_graph_page
from app.ui.components.arch_explorer_page import render_arch_explorer_page
from app.ui.components.exec_navigator_page import render_exec_navigator_page
from app.ui.components.search_page import render_search_page
from app.ui.components.export_page import render_export_page
from app.ui.components.log_viewer_page import render_log_viewer_page
from app.services.chat_service import ChatService
from app.utils.logger import get_logger, setup_logging
from app.tools.repository_tools import clear_tool_cache

setup_logging()
logger = get_logger(__name__)


# Initialize singletons
@st.cache_resource
def get_repository_service():
    return RepositoryService(settings)

@st.cache_resource
def get_chat_service():
    from app.utils.llm_factory import LLMFactory
    chat_settings = settings.model_copy(update={'ollama_model': 'gpt-oss:120b-cloud'})
    return ChatService(LLMFactory.get_llm(chat_settings), chat_settings)

def load_css():
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="RepoLens",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_css()
    repo_service = get_repository_service()
    
    # State management init
    if 'app_state' not in st.session_state:
        if 'analysis_result' in st.session_state:
            st.session_state.app_state = 'repo_dashboard'
        else:
            st.session_state.app_state = 'landing'

    # valid post-landing states
    valid_states = [
        "dashboard", "investigation", "onboarding", "reviewer", "chat", "repo_dashboard", 
        "history", "settings", "analytics", "monitoring", "cache_management", "performance",
        "dep_graph", "arch_explorer", "exec_navigator", "search", "export", "logs"
    ]
    if st.session_state.app_state in valid_states:
        with st.sidebar:
            st.title("RepoLens")
            if 'user_context' in st.session_state:
                ctx = st.session_state['user_context']
                st.write(f"**Role:** {ctx.role.value}")
                
            st.markdown("---")
            st.markdown("## Navigation")
            
            if "analysis_result" in st.session_state:
                if st.button("🏠 Repository Home", type="primary" if st.session_state.app_state == "repo_dashboard" else "secondary"):
                    st.session_state.app_state = "repo_dashboard"
                    st.rerun()
                    
                if st.button("📊 Raw Analysis", type="primary" if st.session_state.app_state == "dashboard" else "secondary"):
                    st.session_state.app_state = "dashboard"
                    st.rerun()
                    
                if st.button("🤖 AI Investigation", type="primary" if st.session_state.app_state == "investigation" else "secondary"):
                    st.session_state.app_state = "investigation"
                    st.rerun()
    
                if "investigation_result" in st.session_state:
                    if st.session_state.investigation_result.onboarding_guide:
                        if st.button("📘 Onboarding Guide", type="primary" if st.session_state.app_state == "onboarding" else "secondary"):
                            st.session_state.app_state = "onboarding"
                            st.rerun()
                    if st.session_state.investigation_result.review_report:
                        if st.button("🔍 Reviewer Dashboard", type="primary" if st.session_state.app_state == "reviewer" else "secondary"):
                            st.session_state.app_state = "reviewer"
                            st.rerun()
                    
                    if st.button("💬 Repository Chat", type="primary" if st.session_state.app_state == "chat" else "secondary"):
                        st.session_state.app_state = "chat"
                        st.rerun()
                        
            st.divider()
            
            # Interactive Explorers
            st.markdown("## Interactive Explorers")
            if "analysis_result" in st.session_state:
                if st.button("🕸️ Dependency Graph", type="primary" if st.session_state.app_state == "dep_graph" else "secondary"):
                    st.session_state.app_state = "dep_graph"
                    st.rerun()
                    
            if "investigation_result" in st.session_state and st.session_state.investigation_result:
                if st.button("🏗️ Architecture Explorer", type="primary" if st.session_state.app_state == "arch_explorer" else "secondary"):
                    st.session_state.app_state = "arch_explorer"
                    st.rerun()
                if st.button("🔄 Execution Navigator", type="primary" if st.session_state.app_state == "exec_navigator" else "secondary"):
                    st.session_state.app_state = "exec_navigator"
                    st.rerun()
                    
                st.divider()
                from app.ui.components.recommendations import render_recommendations
                render_recommendations()

            st.divider()
            
            # Global Nav
            st.markdown("## Management")
            if st.button("🔎 Global Search", type="primary" if st.session_state.app_state == "search" else "secondary"):
                st.session_state.app_state = "search"
                st.rerun()
                
            if st.button("📚 Repository History", type="primary" if st.session_state.app_state == "history" else "secondary"):
                st.session_state.app_state = "history"
                st.rerun()
                
            if st.button("📈 Analytics", type="primary" if st.session_state.app_state == "analytics" else "secondary"):
                st.session_state.app_state = "analytics"
                st.rerun()
                
            if st.button("🛡️ Agent Monitoring", type="primary" if st.session_state.app_state == "monitoring" else "secondary"):
                st.session_state.app_state = "monitoring"
                st.rerun()
                
            if st.button("🗄️ Cache Management", type="primary" if st.session_state.app_state == "cache_management" else "secondary"):
                st.session_state.app_state = "cache_management"
                st.rerun()
                
            if st.button("⏱️ Performance", type="primary" if st.session_state.app_state == "performance" else "secondary"):
                st.session_state.app_state = "performance"
                st.rerun()
                
            if st.button("📤 Export", type="primary" if st.session_state.app_state == "export" else "secondary"):
                st.session_state.app_state = "export"
                st.rerun()
                
            if st.button("📋 Logs", type="primary" if st.session_state.app_state == "logs" else "secondary"):
                st.session_state.app_state = "logs"
                st.rerun()
                
            if st.button("⚙️ Settings", type="primary" if st.session_state.app_state == "settings" else "secondary"):
                st.session_state.app_state = "settings"
                st.rerun()
                
            st.divider()
            if st.button("← Load New Repository"):
                clear_tool_cache()
                # Cleanup temp dir if exists
                if 'temp_dir' in st.session_state:
                    repo_service.cleanup(st.session_state['temp_dir'])
                    del st.session_state['temp_dir']
                    
                st.session_state.app_state = "landing"
                if "analysis_result" in st.session_state:
                    del st.session_state.analysis_result
                if 'user_context' in st.session_state:
                    del st.session_state.user_context
                if "investigation_result" in st.session_state:
                    del st.session_state.investigation_result
                st.rerun()
                
    # Main content rendering based on state
    if st.session_state.app_state == "landing":
        render_landing(repo_service)
    elif st.session_state.app_state == "repo_dashboard":
        if "analysis_result" in st.session_state:
            render_repo_dashboard(st.session_state.analysis_result)
        else:
            st.session_state.app_state = "landing"
            st.rerun()
    elif st.session_state.app_state == "dashboard":
        if "analysis_result" in st.session_state:
            render_dashboard(st.session_state.analysis_result)
        else:
            st.session_state.app_state = "landing"
            st.rerun()
    elif st.session_state.app_state == "investigation":
        if "analysis_result" in st.session_state:
            render_investigation_dashboard(st.session_state.analysis_result)
        else:
            st.session_state.app_state = "landing"
            st.rerun()
    elif st.session_state.app_state == "onboarding":
        if "investigation_result" in st.session_state and st.session_state.investigation_result.onboarding_guide:
            render_onboarding_guide(st.session_state.investigation_result.onboarding_guide)
        else:
            st.session_state.app_state = "investigation"
            st.rerun()
    elif st.session_state.app_state == "reviewer":
        if "investigation_result" in st.session_state and st.session_state.investigation_result.review_report:
            render_reviewer_dashboard(st.session_state.investigation_result.review_report)
        else:
            st.session_state.app_state = "investigation"
            st.rerun()
    elif st.session_state.app_state == "chat":
        if "investigation_result" in st.session_state:
            render_chat_page(get_chat_service())
        else:
            st.session_state.app_state = "investigation"
            st.rerun()
    elif st.session_state.app_state == "history":
        render_repo_history_page()
    elif st.session_state.app_state == "analytics":
        render_analytics_page()
    elif st.session_state.app_state == "monitoring":
        render_monitoring_page()
    elif st.session_state.app_state == "cache_management":
        render_cache_management_page()
    elif st.session_state.app_state == "performance":
        render_performance_page()
    elif st.session_state.app_state == "dep_graph":
        render_dep_graph_page()
    elif st.session_state.app_state == "arch_explorer":
        render_arch_explorer_page()
    elif st.session_state.app_state == "exec_navigator":
        render_exec_navigator_page()
    elif st.session_state.app_state == "search":
        render_search_page()
    elif st.session_state.app_state == "export":
        render_export_page()
    elif st.session_state.app_state == "logs":
        render_log_viewer_page()
    elif st.session_state.app_state == "settings":
        render_settings_page()

if __name__ == "__main__":
    main()
