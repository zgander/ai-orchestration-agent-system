import streamlit as st

def render_recommendations():
    """Renders smart recommendations based on current context."""
    if "investigation_result" not in st.session_state or not st.session_state.investigation_result:
        return
        
    guide = st.session_state.investigation_result.onboarding_guide
    if not guide:
        return
        
    st.markdown("### 💡 Recommendations")
    
    # Files to read
    if guide.reading_order:
        st.markdown("**Next Files to Read:**")
        files_to_read = []
        for day in guide.reading_order:
            files_to_read.extend(day.files)
        for file in files_to_read[:3]:  # Top 3
            st.markdown(f"- `{file}`")
            
    # Key Flows
    if guide.execution_flows:
        st.markdown("**Important Flows:**")
        for flow in guide.execution_flows[:2]:
            st.markdown(f"- {flow.name}")
            
    # Setup
    if guide.setup_guide and guide.setup_guide.installation_steps:
        st.info("Don't forget to check the Setup Guide!")
        
    from app.ui.components.ai_explain import render_explain_button
    st.markdown("**Have Questions?**")
    if st.button("💬 Chat about this repository", use_container_width=True):
        st.session_state.app_state = "chat"
        st.rerun()
