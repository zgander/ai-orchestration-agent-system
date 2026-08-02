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
            
            from app.services.investigation_cache import load_investigation_result, save_investigation_result
            user_role = st.session_state.user_context.role.value if 'user_context' in st.session_state else "Full Stack Developer"
            user_question = st.session_state.user_context.question if 'user_context' in st.session_state and st.session_state.user_context.question else "Give me a comprehensive overview of the architecture and execution flow."
            
            # Check for cached result first
            cached_result = load_investigation_result(analysis_result.repository_info.name, user_role, user_question)
            
            if cached_result and not st.session_state.get("force_rerun_investigation", False):
                cards_placeholder.empty()
                st.success("✅ A recent investigation for this repository and query was found in cache!")
                
                cache_col1, cache_col2 = st.columns(2)
                with cache_col1:
                    if st.button("📂 Load Cached Result", type="primary", use_container_width=True):
                        st.session_state.investigation_result = cached_result
                        if cached_result.onboarding_guide:
                            st.session_state.app_state = "onboarding"
                        st.rerun()
                with cache_col2:
                    if st.button("🔄 Run Fresh Investigation", use_container_width=True):
                        st.session_state.force_rerun_investigation = True
                        st.rerun()
                return  # Stop here — don't run investigation
            
            # Clear the force flag
            st.session_state.pop("force_rerun_investigation", None)
                    
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
                
                # Run the investigation blocking
                # The callback will be called synchronously during the run
                result = service.investigate(
                    analysis_result=analysis_result,
                    user_role="Senior Software Engineer",
                    user_question="Give me a comprehensive overview of the architecture and execution flow.",
                    progress_callback=progress_callback
                )
                
                status.update(label="Investigation Complete", state="complete", expanded=False)
                
            # Save to session state and rerun to show final static view
            st.session_state.investigation_result = result
            st.rerun()
            
        except Exception as e:
            st.error(f"Investigation failed: {e}")
            import traceback
            st.code(traceback.format_exc(), language="python")
