import streamlit as st
from app.ui.components.mermaid_renderer import render_mermaid
from typing import List
from app.models.onboarding_models import ExecutionFlow

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
        
    flows_by_type = {}
    for flow in guide.execution_flows:
        flow_type = getattr(flow, 'flow_type', 'Unknown')
        if flow_type not in flows_by_type:
            flows_by_type[flow_type] = []
        flows_by_type[flow_type].append(flow)
        
    selected_type = st.sidebar.selectbox("Filter by Flow Type", ["All"] + list(flows_by_type.keys()))
    
    display_flows: List[ExecutionFlow] = []
    if selected_type == "All":
        display_flows = guide.execution_flows
    else:
        display_flows = flows_by_type.get(selected_type, [])
        
    if not display_flows:
        st.info("No flows match the selected type.")
        return

    flow_names = [f.name for f in display_flows]
    selected_flow_name = st.selectbox("Select Execution Flow", flow_names)
    
    selected_flow = next((f for f in display_flows if f.name == selected_flow_name), None)
    
    if selected_flow:
        st.markdown(f"### {selected_flow.name}")
        
        # Display Flow Metadata
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.metric("Flow Type", getattr(selected_flow, 'flow_type', 'Unknown'))
        with meta_col2:
            confidence = getattr(selected_flow, 'confidence', 1.0)
            st.metric("Confidence", f"{confidence:.0%}")
        
        if hasattr(selected_flow, 'supporting_files') and selected_flow.supporting_files:
            st.markdown("**Supporting Files:**")
            for f in selected_flow.supporting_files:
                st.write(f"- `{f}`")
        
        st.divider()
        
        col_viz, col_steps = st.columns([1, 1])
        
        with col_viz:
            st.markdown("#### Flow Visualization")
            if selected_flow.mermaid_diagram:
                render_mermaid(selected_flow.mermaid_diagram)
            else:
                # Fallback to generating a simple text-based flow diagram
                diagram = "graph TD\n"
                for i, step in enumerate(selected_flow.steps):
                    step_name = step.get('step', f"Step {i+1}").replace('"', "'")
                    diagram += f"  S{i}[\"{step_name}\"]\n"
                    if i > 0:
                        diagram += f"  S{i-1} --> S{i}\n"
                render_mermaid(diagram)
                
        with col_steps:
            st.markdown("#### Steps")
            for i, step in enumerate(selected_flow.steps):
                with st.expander(f"Step {i+1}: {step.get('step', 'Unknown')}", expanded=True):
                    st.write(step.get('detail', ''))
                    if step.get('file'):
                        st.markdown(f"**File:** `{step['file']}`")

    if hasattr(guide, 'ai_insights') and guide.ai_insights:
        st.divider()
        st.markdown("### 🤖 Execution Insights")
        for insight in guide.ai_insights:
            if "execution" in insight.lower() or "flow" in insight.lower():
                st.write(f"- {insight}")
