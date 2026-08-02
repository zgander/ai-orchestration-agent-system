import streamlit as st
import pandas as pd
from app.services.repository_history import RepositoryHistoryService

def render_analytics_page():
    st.title("📊 Investigation Analytics")
    st.write("Cross-repository insights and metrics.")
    
    try:
        import plotly.express as px
    except ImportError:
        st.error("Plotly is required for the analytics dashboard. Please install it with `pip install plotly`.")
        return
        
    history_service = RepositoryHistoryService()
    repos = history_service.list_repositories()
    
    if not repos:
        st.info("No repositories available for analytics.")
        return
        
    # Prepare data
    data = []
    for r in repos:
        langs = r.tech_stack_summary.get("languages", [])
        primary_lang = langs[0] if langs else "Unknown"
        data.append({
            "Name": r.name,
            "Primary Language": primary_lang,
            "Size (MB)": r.size_bytes / (1024*1024),
            "Status": r.investigation_status.value
        })
        
    df = pd.DataFrame(data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Repositories by Language")
        fig_lang = px.pie(df, names="Primary Language", hole=0.3)
        st.plotly_chart(fig_lang, use_container_width=True)
        
    with col2:
        st.subheader("Repository Size Distribution")
        fig_size = px.histogram(df, x="Size (MB)", nbins=10)
        st.plotly_chart(fig_size, use_container_width=True)
        
    st.divider()
    
    st.subheader("Investigation Status")
    status_counts = df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig_status = px.bar(status_counts, x="Status", y="Count", color="Status")
    st.plotly_chart(fig_status, use_container_width=True)
