import streamlit as st
from app.ui.components.mermaid_renderer import render_mermaid

def render_exec_navigator_page():
    st.title("🔄 Execution Flow Navigator")
    st.write("Step-by-step trace of critical data flows through the application.")
    
    if "investigation_result" not in st.session_state or not st.session_state.investigation_result:
        st.info("No investigation result available. Run an AI investigation first.")
        return
        
    guide = st.session_state.investigation_result.onboarding_guide
    if not guide or not guide.execution_flows:
        st.info("No execution flows were discovered for this repository.")
        return
        
    flow_names = [f.name for f in guide.execution_flows]
    selected_flow_name = st.selectbox("Select Execution Flow", flow_names)
    
    selected_flow = next((f for f in guide.execution_flows if f.name == selected_flow_name), None)
    
    if selected_flow:
        st.markdown(f"### {selected_flow.name}")
        
        col_viz, col_steps = st.columns([1, 1])
        
        with col_viz:
            st.markdown("#### Flow Visualization")
            if selected_flow.mermaid_diagram:
                render_mermaid(selected_flow.mermaid_diagram)
            else:
                st.info("No diagram available for this flow.")
                
        with col_steps:
            st.markdown("#### Steps")
            for i, step in enumerate(selected_flow.steps):
                with st.expander(f"Step {i+1}: {step.get('component', 'Unknown')}"):
                    st.write(step.get('description', ''))
                    if step.get('file'):
                        st.markdown(f"**File:** `{step['file']}`")
                        
                    # Here we could link to the actual code if we had a code viewer
                    # e.g., if st.button(f"View Code for Step {i+1}"): ...
