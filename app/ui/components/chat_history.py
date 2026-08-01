import streamlit as st
from typing import List
from app.models.chat_models import ChatSession

def render_chat_history(sessions: List[ChatSession]):
    st.sidebar.markdown("### Chat History")
    
    if not sessions:
        st.sidebar.info("No previous chats for this repository.")
        return
        
    for session in sessions:
        # Display the first user message as the title, or a default
        title = "New Chat"
        if session.messages:
            for msg in session.messages:
                if msg.role == "user":
                    title = msg.content[:30] + ("..." if len(msg.content) > 30 else "")
                    break
                    
        date_str = session.updated_at.strftime("%b %d, %H:%M")
        
        if st.sidebar.button(f"{title}\n\n*{date_str}*", key=f"hist_{session.session_id}", use_container_width=True):
            st.session_state.current_chat_session_id = session.session_id
            st.rerun()
            
    if st.sidebar.button("+ New Chat", use_container_width=True, type="primary"):
        st.session_state.current_chat_session_id = None
        st.rerun()
