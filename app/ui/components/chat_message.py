import streamlit as st
from app.models.chat_models import ChatMessage
from app.ui.components.chat_citation import render_citation

def render_chat_message(message: ChatMessage):
    with st.chat_message(message.role):
        st.markdown(message.content)
        
        if message.citations:
            with st.expander("Sources & Citations"):
                for citation in message.citations:
                    render_citation(citation)
                    st.divider()
