import streamlit as st
from app.services.export_service import ExportService
from app.models.history_models import ExportConfig, ExportFormat
from app.config.settings import settings

def render_export_page():
    st.title("📤 Export Center")
    st.write("Download investigation results and onboarding guides.")
    
    if "investigation_result" not in st.session_state or not st.session_state.investigation_result:
        st.info("No investigation result available to export.")
        return
        
    result = st.session_state.investigation_result
    export_service = ExportService()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Export Options")
        
        format_str = st.radio(
            "Format", 
            ["Markdown", "JSON", "Bundle (ZIP)"],
            index=["MARKDOWN", "JSON", "BUNDLE"].index(settings.export_format)
        )
        
        format_map = {
            "Markdown": ExportFormat.MARKDOWN,
            "JSON": ExportFormat.JSON,
            "Bundle (ZIP)": ExportFormat.BUNDLE
        }
        
        fmt = format_map[format_str]
        
        sections = []
        if fmt in [ExportFormat.MARKDOWN, ExportFormat.BUNDLE]:
            st.markdown("**Sections to Include**")
            sec_arch = st.checkbox("Architecture", value=True)
            sec_folder = st.checkbox("Folder Guide", value=True)
            sec_flows = st.checkbox("Execution Flows", value=True)
            sec_api = st.checkbox("API Explorer", value=True)
            sec_setup = st.checkbox("Setup & Environment", value=True)
            
            if sec_arch: sections.append("Architecture")
            if sec_folder: sections.append("Folder Guide")
            if sec_flows: sections.append("Execution Flows")
            if sec_api: sections.append("API Explorer")
            if sec_setup: sections.append("Setup & Environment")
            
        include_evidence = st.checkbox("Include Evidence", value=True)
        include_diagrams = st.checkbox("Include Diagrams (Mermaid)", value=True)
        
    with col2:
        st.subheader("Generate")
        if st.button("Prepare Export", type="primary", use_container_width=True):
            config = ExportConfig(
                format=fmt,
                sections=sections,
                include_evidence=include_evidence,
                include_diagrams=include_diagrams
            )
            
            with st.spinner("Generating export file..."):
                filename, content = export_service.export(result, config)
                
                mime_map = {
                    ExportFormat.MARKDOWN: "text/markdown",
                    ExportFormat.JSON: "application/json",
                    ExportFormat.BUNDLE: "application/zip"
                }
                
                st.download_button(
                    label=f"Download {filename}",
                    data=content,
                    file_name=filename,
                    mime=mime_map[fmt],
                    use_container_width=True
                )
