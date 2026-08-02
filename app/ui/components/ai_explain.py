import streamlit as st
from typing import Optional

def render_explain_button(topic: str, context: Optional[str] = None, key: Optional[str] = None):
    """
    Renders an 'Explain This' button that pre-fills the chat with a question
    about the given topic.
    """
    if st.button("🤖 Explain This", key=f"explain_{key or hash(topic)}", size="small"):
        if "investigation_result" not in st.session_state:
            st.error("AI Investigation must be run first.")
            return
            
        prompt = f"Please explain {topic} in detail."
        if context:
            prompt += f" Context: {context}"
            
        # Set the prompt in session state for the chat page to pick up
        st.session_state.initial_chat_prompt = prompt
        st.session_state.app_state = "chat"
        st.rerun()
