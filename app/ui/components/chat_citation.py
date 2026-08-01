import streamlit as st
from app.models.chat_models import Citation, CitationType
from app.ui.components.evidence_viewer import render_evidence

def render_citation(citation: Citation):
    if citation.type == CitationType.SECTION:
        st.markdown(f"📖 **Section:** {citation.display_text}")
    elif citation.type == CitationType.FILE:
        st.markdown(f"📄 **File:** `{citation.reference}`")
        if st.button(f"View {citation.display_text}", key=f"btn_{citation.reference}"):
            st.session_state.active_code_viewer = citation.reference
    elif citation.type == CitationType.FINDING:
        st.markdown(f"🔍 **Finding:** {citation.display_text}")
    elif citation.type == CitationType.EVIDENCE:
        st.markdown(f"📎 **Evidence:** {citation.display_text}")
