import streamlit as st
from typing import List

from app.models.investigation_models import TimelineEvent

def render_timeline(events: List[TimelineEvent]):
    st.markdown("### ⏱️ Timeline")
    
    # Custom CSS for timeline
    st.markdown("""
    <style>
    .timeline-event {
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        margin-bottom: 10px;
    }
    .timeline-time {
        font-family: monospace;
        color: #888;
        margin-right: 15px;
        min-width: 70px;
    }
    .timeline-content {
        flex: 1;
    }
    .timeline-detail {
        font-size: 0.9em;
        color: #666;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    for event in reversed(events):
        time_str = event.timestamp.strftime("%H:%M:%S")
        
        # Agent icons
        icon = "🤖"
        if event.agent_type.value == "SUPERVISOR": icon = "👔"
        elif event.agent_type.value == "ARCHITECTURE": icon = "🏗️"
        elif event.agent_type.value == "EXECUTION_FLOW": icon = "🔄"
        elif event.agent_type.value == "API_DATA": icon = "🌐"
        elif event.agent_type.value == "SETUP": icon = "⚙️"
        
        detail_html = f'<div class="timeline-detail">{event.detail}</div>' if event.detail else ""
        
        html = f"""
        <div class="timeline-event">
            <div class="timeline-time">{time_str}</div>
            <div class="timeline-content">
                <strong>{icon} {event.event}</strong>
                {detail_html}
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
