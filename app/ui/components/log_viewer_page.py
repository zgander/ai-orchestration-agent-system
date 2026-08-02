import streamlit as st
import pandas as pd
from app.utils.logger import StructuredLogStore

def render_log_viewer_page():
    st.title("📋 System Logs")
    st.write("View and filter internal system logs.")
    
    store = StructuredLogStore.get_instance()
    
    col1, col2 = st.columns(2)
    with col1:
        cat = st.selectbox("Category", ["All", "investigation", "chat", "review", "cache", "tool", "llm", "general"])
    with col2:
        lvl = st.selectbox("Level", ["All", "DEBUG", "INFO", "WARNING", "ERROR"])
        
    logs = store.get_logs(category=cat, level=lvl)
    
    if not logs:
        st.info("No logs match the selected filters.")
        return
        
    df = pd.DataFrame(logs)
    # Reorder columns
    df = df[["timestamp", "level", "category", "logger_name", "message"]]
    
    st.dataframe(
        df,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Time", format="YYYY-MM-DD HH:mm:ss"),
            "level": st.column_config.TextColumn("Level"),
            "category": st.column_config.TextColumn("Category"),
            "logger_name": st.column_config.TextColumn("Logger"),
            "message": st.column_config.TextColumn("Message", width="large")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.download_button(
        label="Download Logs (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="repolens_logs.csv",
        mime="text/csv"
    )
