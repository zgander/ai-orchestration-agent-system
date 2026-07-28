import streamlit as st
import pandas as pd
from typing import List

from app.models.analysis_models import AnalysisResult
from app.ui.components.tree_view import render_repository_tree
from app.ui.components.tech_stack_view import render_tech_stack
from app.ui.components.api_view import render_api_endpoints

def render_dashboard(result: AnalysisResult):
    repo = result.repository_info
    stats = result.statistics
    
    st.title("Repository Analysis Dashboard")
    
    # AI Investigation Button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Analysis complete. You can explore the raw data below, or start the AI Investigation Engine to get a high-level architectural overview.")
    with col2:
        if st.button("🤖 Start AI Investigation", type="primary"):
            st.session_state.app_state = "investigation"
            st.rerun()
            
    st.divider()

    # Metrics Row  # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Source", repo.source.source_type.value)
    col2.metric("Total Files", stats.total_files)
    col3.metric("Source Files", stats.total_source_files)
    col4.metric("Analysis Time", f"{result.duration_seconds:.2f}s")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview & Tech Stack", 
        "Entry Points & APIs", 
        "Environment", 
        "Repository Tree",
        "Dependency Graph"
    ])
    
    with tab1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("Tech Stack")
            render_tech_stack(result.tech_stack)
            
        with col_right:
            st.subheader("Statistics")
            if stats.languages_breakdown:
                st.write("**Languages**")
                df = pd.DataFrame(list(stats.languages_breakdown.items()), columns=["Language", "Files"])
                st.bar_chart(df.set_index("Language"))
                
            if stats.largest_dirs:
                st.write("**Largest Directories**")
                st.dataframe(
                    pd.DataFrame(list(stats.largest_dirs.items()), columns=["Directory", "Size (Bytes)"]),
                    hide_index=True
                )

    with tab2:
        st.subheader("Application Entry Points")
        if result.entry_points:
            ep_data = []
            for ep in result.entry_points:
                ep_data.append({
                    "Confidence": f"{ep.confidence:.0%}",
                    "File": ep.file_path,
                    "Line": ep.line_number,
                    "Description": ep.description
                })
            st.dataframe(pd.DataFrame(ep_data), hide_index=True)
        else:
            st.info("No entry points confidently detected.")
            
        st.markdown("---")
        render_api_endpoints(result.api_endpoints)
        
    with tab3:
        st.subheader("Environment Variables")
        if result.env_variables:
            env_data = []
            for env in result.env_variables:
                env_data.append({
                    "Variable Name": env.name,
                    "Found In": f"{env.file_path}:{env.line_number}",
                    "Access Method": env.access_method
                })
            st.dataframe(pd.DataFrame(env_data), hide_index=True)
        else:
            st.info("No environment variables detected.")
            
    with tab4:
        render_repository_tree(result.tree.root)
        
    with tab5:
        st.subheader("Dependency Graph")
        deps = result.dependency_graph
        
        st.metric("Connected Components", deps.connected_components)
        
        if deps.most_connected:
            st.write("**Most Connected Files (Hubs)**")
            for f in deps.most_connected:
                st.markdown(f"- `{f}`")
                
        # We don't render the full graph visually in Phase 1 as it can be huge and requires D3/Cytoscape
        st.info("Graph analysis complete. Advanced visualisations will be available in future phases.")
