import streamlit as st
import pandas as pd
from app.utils.performance_tracker import PerformanceTracker

def render_performance_page():
    st.title("⏱️ Performance Dashboard")
    st.write("Real-time metrics for the current session.")
    
    tracker = PerformanceTracker()
    metrics = tracker.get_metrics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Repo Load Time", f"{metrics.repo_load_time_seconds:.2f}s")
    col2.metric("Analysis Duration", f"{metrics.analysis_duration_seconds:.2f}s")
    
    total_cache = metrics.cache_hits + metrics.cache_misses
    hit_ratio = (metrics.cache_hits / total_cache * 100) if total_cache > 0 else 0
    col3.metric("Cache Hit Ratio", f"{hit_ratio:.1f}%", f"{metrics.cache_hits} hits / {metrics.cache_misses} misses")
    
    st.divider()
    
    st.subheader("Agent Durations")
    if metrics.agent_durations:
        df_agents = pd.DataFrame(list(metrics.agent_durations.items()), columns=["Agent", "Duration (s)"])
        st.bar_chart(df_agents.set_index("Agent"))
    else:
        st.info("No agents have run in this session.")
        
    st.subheader("Phase 3 Durations")
    col_p1, col_p2 = st.columns(2)
    col_p1.metric("Reviewer Duration", f"{metrics.reviewer_duration_seconds:.2f}s")
    col_p2.metric("Synthesis Duration", f"{metrics.synthesis_duration_seconds:.2f}s")
    
    st.subheader("Chat Latency")
    if metrics.chat_latencies:
        df_chat = pd.DataFrame({"Latency (s)": metrics.chat_latencies})
        st.line_chart(df_chat)
        avg_chat = sum(metrics.chat_latencies) / len(metrics.chat_latencies)
        st.write(f"**Average Chat Latency:** {avg_chat:.2f}s")
    else:
        st.info("No chat messages sent in this session.")
        
    st.divider()
    
    if st.button("Reset Session Metrics"):
        tracker.reset()
        st.rerun()
