import streamlit as st
from app.ui.components.mermaid_renderer import render_mermaid

def render_arch_explorer_page():
    st.title("🏗️ Architecture Explorer")
    st.write("Explore the structural components of the codebase.")
    
    if "investigation_result" not in st.session_state or not st.session_state.investigation_result:
        st.info("No investigation result available. Run an AI investigation first.")
        return
        
    guide = st.session_state.investigation_result.onboarding_guide
    if not guide:
        st.info("No onboarding guide available.")
        return
        
    st.markdown("### Mental Model")
    st.info(guide.mental_model)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Architecture Diagram")
        if guide.architecture_diagram:
            render_mermaid(guide.architecture_diagram)
        else:
            st.write("No architecture diagram available.")
            
        st.markdown("### Explanation")
        st.write(guide.architecture_explanation)
        
    with col2:
        st.markdown("### Folders by Architecture")
        # We can map folders to their purposes as a proxy for components
        for folder in guide.folder_guide:
            if folder.importance in ["critical", "high"]:
                with st.expander(f"📁 {folder.path}"):
                    st.write(folder.purpose)
                    
                    # See if there are any APIs in this folder
                    folder_apis = [api for api in guide.api_explorer if folder.path in api.handler_file]
                    if folder_apis:
                        st.markdown("**APIs:**")
                        for api in folder_apis:
                            st.write(f"- `{api.method} {api.path}`")
