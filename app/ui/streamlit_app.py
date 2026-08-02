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
from app.utils.logger import get_logger
from app.tools.repository_tools import clear_tool_cache

logger = get_logger(__name__)

# Initialize singletons
@st.cache_resource
def get_repository_service():
    return RepositoryService(settings)

@st.cache_resource
def get_chat_service():
    from app.utils.llm_factory import LLMFactory
    from app.config.settings import Settings
    s = Settings()
    return ChatService(LLMFactory.get_llm(s), s)

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
            st.session_state.app_state = 'dashboard'
        else:
            st.session_state.app_state = 'landing'

    if st.session_state.app_state in ["dashboard", "investigation"]:
        with st.sidebar:
            st.title("RepoLens")
            if 'user_context' in st.session_state:
                ctx = st.session_state['user_context']
                st.write(f"**Role:** {ctx.role.value}")
                
            st.markdown("---")
            st.markdown("## Navigation")
            if st.button("📊 Raw Analysis", type="primary" if st.session_state.app_state == "dashboard" else "secondary"):
                st.session_state.app_state = "dashboard"
                st.rerun()
                
            if st.button("🤖 AI Investigation", type="primary" if st.session_state.app_state == "investigation" else "secondary"):
                st.session_state.app_state = "investigation"
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

if __name__ == "__main__":
    main()
