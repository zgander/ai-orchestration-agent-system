import streamlit as st
from typing import Optional

from app.config.settings import Settings

def render_mermaid(diagram: str, fallback_ascii: Optional[str] = None):
    settings = Settings()
    if settings.enable_mermaid_diagrams and diagram:
        # Streamlit 1.33+ supports mermaid natively inside markdown codeblocks
        st.markdown(f"```mermaid\n{diagram}\n```")
    elif fallback_ascii:
        st.code(fallback_ascii, language="text")
    else:
        st.info("No diagram available.")
