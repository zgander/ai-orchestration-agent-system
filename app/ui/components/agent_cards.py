import streamlit as st
from typing import Dict, Optional, Set

from app.models.investigation_models import AgentType, AgentReport, AgentStatus

def render_agent_cards(agent_reports: Dict[AgentType, AgentReport], current_running: Optional[AgentType] = None, completed_agents: Optional[Set[AgentType]] = None):
    if completed_agents is None:
        completed_agents = set()
    cols = st.columns(4)
    
    agents = [
        (AgentType.ARCHITECTURE, "🏗️ Arch", cols[0]),
        (AgentType.EXECUTION_FLOW, "🔄 Exec", cols[1]),
        (AgentType.API_DATA, "🌐 API", cols[2]),
        (AgentType.SETUP, "⚙️ Setup", cols[3])
    ]
    
    for agent_type, title, col in agents:
        with col:
            report = agent_reports.get(agent_type)
            
            # Determine state
            if report and report.status == AgentStatus.FAILED:
                status_color = "red"
                status_text = "Failed"
                detail = "Check errors"
            elif (report and report.status == AgentStatus.COMPLETED) or (agent_type in completed_agents):
                status_color = "green"
                status_text = "Completed"
                detail = f"{len(report.findings)} findings" if report else "Findings ready"
            elif agent_type == current_running or (report and report.status == AgentStatus.RUNNING):
                status_color = "blue"
                status_text = "Running"
                detail = "Investigating..."
            else:
                status_color = "gray"
                status_text = "Idle"
                detail = "Waiting..."
                
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:10px; margin-bottom:10px; background-color: rgba(255,255,255,0.05);">
                <div style="font-weight:bold; font-size:1.1em; margin-bottom:5px;">{title}</div>
                <div style="color:{status_color}; font-size:0.9em;">⬤ {status_text}</div>
                <div style="font-size:0.8em; color:#888; margin-top:5px;">{detail}</div>
            </div>
            """, unsafe_allow_html=True)
