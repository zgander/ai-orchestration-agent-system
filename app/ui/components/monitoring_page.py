import streamlit as st
import pandas as pd
import json
from app.services.investigation_cache import CACHE_DIR

def render_monitoring_page():
    st.title("🛡️ Agent Monitoring")
    st.write("Deep dive into agent execution, tool usage, and workflow.")
    
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError:
        st.error("Plotly is required for the monitoring dashboard. Please install it with `pip install plotly`.")
        return
        
    # Get available repos
    repo_options = []
    if CACHE_DIR.exists():
        repo_options = [f.stem for f in CACHE_DIR.glob("*.json")]
        
    if not repo_options:
        st.info("No investigation data available to monitor.")
        return
        
    selected_repo = st.selectbox("Select Investigation to Monitor", repo_options)
    
    try:
        with open(CACHE_DIR / f"{selected_repo}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Failed to load data for {selected_repo}: {e}")
        return
        
    # 1. Timeline Chart (Gantt)
    st.subheader("Execution Timeline")
    timeline_data = []
    
    reports = data.get("agent_reports", {})
    for agent, rep in reports.items():
        if "started_at" in rep and "completed_at" in rep and rep["completed_at"]:
            timeline_data.append(dict(
                Task=agent,
                Start=rep["started_at"],
                Finish=rep["completed_at"],
                Resource=agent
            ))
            
    if timeline_data:
        df_timeline = pd.DataFrame(timeline_data)
        fig_timeline = px.timeline(df_timeline, x_start="Start", x_end="Finish", y="Task", color="Resource")
        fig_timeline.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.write("No timeline data available.")
        
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tool Usage Frequency")
        tool_counts = {}
        for agent, rep in reports.items():
            for call in rep.get("tool_calls", []):
                tool = call.get("tool_name")
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
        if tool_counts:
            df_tools = pd.DataFrame(list(tool_counts.items()), columns=["Tool", "Calls"])
            fig_tools = px.pie(df_tools, values="Calls", names="Tool", hole=0.4)
            st.plotly_chart(fig_tools, use_container_width=True)
        else:
            st.write("No tool usage data available.")
            
    with col2:
        st.subheader("Tool Latency")
        tool_latency = []
        for agent, rep in reports.items():
            for call in rep.get("tool_calls", []):
                tool = call.get("tool_name")
                dur = call.get("duration_seconds", 0)
                tool_latency.append({"Tool": tool, "Latency (s)": dur})
                
        if tool_latency:
            df_lat = pd.DataFrame(tool_latency)
            fig_lat = px.box(df_lat, x="Tool", y="Latency (s)")
            st.plotly_chart(fig_lat, use_container_width=True)
        else:
            st.write("No tool latency data available.")
            
    st.divider()
    
    st.subheader("Workflow Visualization")
    # Simplified Mermaid graph of the LangGraph workflow based on actual execution
    mermaid_code = """
    graph TD
        S[Supervisor] --> A[Architecture]
        S --> E[Execution Flow]
        S --> API[API Data]
        S --> SET[Setup]
        A --> M[Merge Results]
        E --> M
        API --> M
        SET --> M
        M --> R[Reviewer]
        R --> SYN[Synthesizer]
    """
    
    from app.ui.components.mermaid_renderer import render_mermaid
    render_mermaid(mermaid_code)
