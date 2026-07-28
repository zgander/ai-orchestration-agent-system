import streamlit as st
from typing import List

from app.models.investigation_models import Evidence

def render_evidence(evidence: List[Evidence], expandable: bool = True):
    if not evidence:
        st.write("No evidence provided.")
        return

    for idx, ev in enumerate(evidence):
        if expandable:
            with st.expander(f"Evidence {idx + 1}: {ev.file_path or 'Unknown Source'} ({ev.source_tool})"):
                _render_evidence_body(ev)
        else:
            st.markdown(f"**Evidence {idx + 1}: {ev.file_path or 'Unknown Source'} ({ev.source_tool})**")
            _render_evidence_body(ev)
            st.divider()

def _render_evidence_body(ev: Evidence):
    if ev.file_path:
        st.markdown(f"**File:** `{ev.file_path}`")
    if ev.line_numbers:
        st.markdown(f"**Lines:** `{ev.line_numbers}`")
    if ev.symbol:
        st.markdown(f"**Symbol:** `{ev.symbol}`")
        
    st.markdown(f"**Relevance:** {ev.relevance}")
    
    if ev.content:
        st.code(ev.content, language="python" if ev.file_path and ev.file_path.endswith(".py") else "text")
