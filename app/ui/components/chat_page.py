import streamlit as st
from app.services.chat_service import ChatService
from app.ui.components.chat_message import render_chat_message
from app.ui.components.chat_history import render_chat_history
from app.ui.components.code_viewer import render_code_viewer

def render_chat_page(chat_service: ChatService):
    st.title("💬 Repository Chat")
    
    repo_name = st.session_state.repository_info.name
    repo_path = st.session_state.repository_info.local_path
    
    st.markdown(f"**repo:** `{repo_name}`")
    st.divider()
    
    # Init session states for chat
    if "current_chat_session_id" not in st.session_state:
        st.session_state.current_chat_session_id = None
    if "active_code_viewer" not in st.session_state:
        st.session_state.active_code_viewer = None
        
    # Render Sidebar History
    sessions = chat_service.get_session_history(repo_name)
    render_chat_history(sessions)
    
    # Sidebar navigation back
    st.sidebar.divider()
    if st.sidebar.button("← Back to Guide", use_container_width=True):
        st.session_state.app_state = "onboarding"
        st.rerun()
        
    # If code viewer is active, show it
    if st.session_state.active_code_viewer:
        render_code_viewer(st.session_state.active_code_viewer)
        return
        
    # Load current session
    current_session = chat_service.memory.get_or_create_session(st.session_state.current_chat_session_id, repo_name)
    st.session_state.current_chat_session_id = current_session.session_id
    
    # Display messages
    for msg in current_session.messages:
        render_chat_message(msg)
        
    # Chat input
    if prompt := st.chat_input("Ask a question about the repository..."):
        # Display user message immediately
        from app.models.chat_models import ChatMessage
        temp_user_msg = ChatMessage(role="user", content=prompt)
        render_chat_message(temp_user_msg)
        
        with st.spinner("Thinking..."):
            # Check if investigation state exists
            if not getattr(st.session_state, "investigation_result", None):
                st.error("No investigation result found. Please run the AI Investigation first.")
                return
                
            response, updated_session = chat_service.ask(
                message=prompt,
                repository_name=repo_name,
                repository_path=repo_path,
                analysis_result_json=st.session_state.analysis_result.model_dump_json(),
                investigation_result_json=st.session_state.investigation_result.model_dump_json(),
                session_id=current_session.session_id
            )
            
            st.rerun()
