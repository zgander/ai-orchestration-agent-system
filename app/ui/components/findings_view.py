import streamlit as st
from typing import Dict, List

from app.models.investigation_models import AgentReport, AgentFinding, AgentType

def render_findings(agent_reports: Dict[AgentType, AgentReport]):
    st.markdown("### 🔍 Investigation Findings")
    
    if not agent_reports:
        st.info("No findings available yet. The agents are still investigating.")
        return
        
    for agent_type, report in agent_reports.items():
        icon = "🤖"
        if agent_type == AgentType.ARCHITECTURE: icon = "🏗️ Architecture"
        elif agent_type == AgentType.EXECUTION_FLOW: icon = "🔄 Execution Flow"
        elif agent_type == AgentType.API_DATA: icon = "🌐 API & Data"
        elif agent_type == AgentType.SETUP: icon = "⚙️ Setup & Environment"
        
        if report.error:
            st.error(f"{icon} Agent failed: {report.error}")
            continue
            
        if not report.findings:
            st.warning(f"{icon} Agent completed but returned no findings.")
            continue
            
        with st.expander(f"{icon} Findings ({len(report.findings)})", expanded=True):
            for finding in report.findings:
                confidence_color = "green" if finding.confidence > 0.8 else ("orange" if finding.confidence > 0.5 else "red")
                
                st.markdown(f"#### {finding.title}")
                st.markdown(f"**Category:** {finding.category} | **Confidence:** :{confidence_color}[{finding.confidence:.2f}]")
                st.markdown(finding.description)
                
                if finding.evidence:
                    st.markdown("**Evidence:**")
                    for idx, ev in enumerate(finding.evidence):
                        file_link = f"[{ev.file_path}](#)" if ev.file_path else "Unknown source"
                        st.markdown(f"{idx+1}. **{file_link}** ({ev.source_tool}): {ev.relevance}")
                        if ev.content:
                            with st.container():
                                st.code(ev.content, language="plaintext")
                st.divider()
