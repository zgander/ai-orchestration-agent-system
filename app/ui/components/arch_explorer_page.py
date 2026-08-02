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

        if hasattr(guide, 'architecture_layers') and guide.architecture_layers:
            st.markdown("### Architecture Layers")
            for layer in sorted(guide.architecture_layers, key=lambda x: x.order):
                with st.expander(f"Layer {layer.order}: {layer.name}", expanded=True):
                    st.write(f"**Purpose:** {layer.purpose}")
                    st.write(f"**Components:** {', '.join(layer.components)}")

        if hasattr(guide, 'component_cards') and guide.component_cards:
            st.markdown("### Component Cards")
            for card in guide.component_cards:
                with st.expander(f"🧩 {card.name}"):
                    st.write(f"**Purpose:** {card.purpose}")
                    if card.responsibilities:
                        st.markdown("**Responsibilities:**")
                        for resp in card.responsibilities:
                            st.write(f"- {resp}")
                    
                    st.markdown("**Connections:**")
                    conn_col1, conn_col2 = st.columns(2)
                    with conn_col1:
                        if card.consumes:
                            st.write(f"**Consumes:** {', '.join(card.consumes)}")
                        if card.dependencies:
                            st.write(f"**Dependencies:** {', '.join(card.dependencies)}")
                    with conn_col2:
                        if card.produces:
                            st.write(f"**Produces:** {', '.join(card.produces)}")
                        if card.used_by:
                            st.write(f"**Used By:** {', '.join(card.used_by)}")

    with col2:
        st.markdown("### Folder Responsibilities")
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

        if hasattr(guide, 'dependency_insights') and guide.dependency_insights:
            st.markdown("### Dependency Insights")
            for insight in guide.dependency_insights:
                st.info(f"**{insight.insight_type}** ({insight.module}): {insight.explanation}")

        if guide.reading_order:
            st.markdown("### Suggested Reading Order")
            for day in guide.reading_order:
                with st.expander(f"Step {day.day}: {day.theme}"):
                    for topic in day.topics:
                        st.write(f"- {topic}")
                    if day.files:
                        st.markdown("**Key Files:**")
                        for f in day.files:
                            st.write(f"`{f}`")

    if hasattr(guide, 'ai_insights') and guide.ai_insights:
        st.divider()
        st.markdown("### 🤖 AI Architecture Insights")
        for insight in guide.ai_insights:
            st.write(f"- {insight}")
