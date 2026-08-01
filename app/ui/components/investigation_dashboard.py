import streamlit as st
import time
from typing import Optional

from app.models.analysis_models import AnalysisResult
from app.models.investigation_models import InvestigationResult, TimelineEvent
from app.services.investigation_service import InvestigationService
from app.config.settings import Settings

from app.ui.components.agent_cards import render_agent_cards
from app.ui.components.timeline_view import render_timeline
from app.ui.components.findings_view import render_findings
from app.tools.repository_tools import clear_tool_cache

def render_investigation_dashboard(analysis_result: AnalysisResult):
    st.title(f"🤖 AI Investigation: {analysis_result.repository_info.name}")
    
    # Check if investigation is already complete and cached in session state
    if "investigation_result" in st.session_state:
        result: InvestigationResult = st.session_state.investigation_result
        
        # Render static completed dashboard
        render_agent_cards(result.agent_reports)
        st.divider()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            render_timeline(result.timeline)
        with col2:
            render_findings(result.agent_reports)
            
        if st.button("📘 View Onboarding Guide", type="primary"):
            st.session_state.app_state = "onboarding"
            st.rerun()

        if st.button("🔄 Rerun Investigation"):
            clear_tool_cache()
            del st.session_state.investigation_result
            st.rerun()
            
    else:
        # Define placeholders for dynamic updates
        cards_placeholder = st.empty()
        st.divider()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            timeline_placeholder = st.empty()
        with col2:
            status_placeholder = st.empty()
            
        # Initial state
        cards_placeholder.write("Initialising agents...")
        
        try:
            settings = Settings()
            service = InvestigationService(settings)
            
            with status_placeholder.status("Running AI Investigation...", expanded=True) as status:
                st.write("Initializing...")
                
                # We need a closure to capture timeline events and update the UI
                timeline_events = []
                
                def progress_callback(events: list[TimelineEvent]):
                    timeline_events.clear()
                    timeline_events.extend(events)
                    
                    # Update timeline UI
                    with timeline_placeholder.container():
                        render_timeline(timeline_events)
                        
                    # Track which agents have completed
                    completed_agents = set()
                    for ev in events:
                        if "completed" in ev.event.lower():
                            completed_agents.add(ev.agent_type)
                            
                    # Update status text
                    if events:
                        latest = events[-1]
                        st.write(f"{latest.agent_type.value}: {latest.event}")
                        
                        # Update cards
                        with cards_placeholder.container():
                            render_agent_cards({}, current_running=latest.agent_type, completed_agents=completed_agents)
                
                user_role = st.session_state.user_context.role.value if 'user_context' in st.session_state else "Full Stack Developer"
                user_question = st.session_state.user_context.question if 'user_context' in st.session_state and st.session_state.user_context.question else "Give me a comprehensive overview of the architecture and execution flow."
                
                # Run the investigation blocking
                # The callback will be called synchronously during the run
                result = service.investigate(
                    analysis_result=analysis_result,
                    user_role=user_role,
                    user_question=user_question,
                    progress_callback=progress_callback
                )
                
                status.update(label="Investigation Complete", state="complete", expanded=False)
                
            # Save to session state
            st.session_state.investigation_result = result
            
            # If onboarding guide was generated successfully, navigate to it automatically
            if result.onboarding_guide:
                st.session_state.app_state = "onboarding"
                
            st.rerun()
            
        except Exception as e:
            st.error(f"Investigation failed: {e}")
            import traceback
            st.code(traceback.format_exc(), language="python")
