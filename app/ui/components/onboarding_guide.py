import streamlit as st
import pandas as pd

from app.models.onboarding_models import OnboardingGuide, DocumentationGap
from app.ui.components.evidence_viewer import render_evidence
from app.ui.components.mermaid_renderer import render_mermaid

def render_onboarding_guide(guide: OnboardingGuide):
    st.title("📘 Interactive Onboarding Guide")
    st.markdown(f"**Generated for:** {guide.role.value}")
    st.markdown(f"**Last updated:** {guide.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    st.divider()

    # Sidebar Navigation within Onboarding Guide
    st.sidebar.markdown("### Guide Sections")
    section = st.sidebar.radio(
        "Navigate",
        [
            "Overview",
            "Architecture",
            "Folder Guide & Files",
            "Execution Flows",
            "API Explorer",
            "Reading Roadmap",
            "Setup & Environment",
            "Documentation Gaps",
            "Confidence Indicators"
        ]
    )

    if section == "Overview":
        _render_overview(guide)
    elif section == "Architecture":
        _render_architecture(guide)
    elif section == "Folder Guide & Files":
        _render_folders(guide)
    elif section == "Execution Flows":
        _render_execution_flows(guide)
    elif section == "API Explorer":
        _render_api_explorer(guide)
    elif section == "Reading Roadmap":
        _render_reading_roadmap(guide)
    elif section == "Setup & Environment":
        _render_setup(guide)
    elif section == "Documentation Gaps":
        _render_gaps(guide)
    elif section == "Confidence Indicators":
        _render_confidence(guide)

def _render_overview(guide: OnboardingGuide):
    st.header("Repository Overview")
    
    st.info(f"**Mental Model:**\n\n{guide.mental_model}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Languages", ", ".join(guide.repository_overview.languages) if guide.repository_overview.languages else "N/A")
    col2.metric("Frameworks", ", ".join(guide.repository_overview.frameworks) if guide.repository_overview.frameworks else "N/A")
    col3.metric("Architecture Style", guide.repository_overview.architecture_style)
    
    st.markdown("### Statistics")
    stats = guide.repository_overview.statistics
    st.json(stats)

def _render_architecture(guide: OnboardingGuide):
    st.header("Architecture Explanation")
    st.markdown(guide.architecture_explanation)
    
    if guide.architecture_diagram:
        st.subheader("Architecture Diagram")
        render_mermaid(guide.architecture_diagram)

def _render_folders(guide: OnboardingGuide):
    st.header("Folder Guide")
    for folder in guide.folder_guide:
        badge_color = "green" if folder.importance == "high" else "orange" if folder.importance == "medium" else "grey"
        read_badge = " **(Read First)**" if folder.read_first else ""
        
        with st.expander(f"📂 {folder.path} - :{badge_color}[{folder.importance.upper()}]{read_badge}"):
            st.markdown(folder.purpose)
            if folder.evidence:
                render_evidence(folder.evidence, expandable=False)
                
    st.header("Important Files")
    if guide.important_files:
        for file in sorted(guide.important_files, key=lambda x: x.rank):
            with st.expander(f"#{file.rank} - 📄 {file.file_path}"):
                st.markdown(f"**Purpose:** {file.purpose}")
                st.markdown(f"**Why it matters:** {file.why_it_matters}")
                st.markdown(f"**Dependencies:** {', '.join(file.dependencies)}")
                if file.evidence:
                     render_evidence(file.evidence, expandable=False)

def _render_execution_flows(guide: OnboardingGuide):
    st.header("Execution Flows")
    if not guide.execution_flows:
        st.info("No execution flows generated.")
        return
        
    flow_names = [f.name for f in guide.execution_flows]
    selected_flow = st.selectbox("Select Flow to Explore", flow_names)
    
    for flow in guide.execution_flows:
        if flow.name == selected_flow:
            if flow.mermaid_diagram:
                render_mermaid(flow.mermaid_diagram)
                st.divider()
                
            st.subheader("Steps")
            for idx, step in enumerate(flow.steps):
                st.markdown(f"**{idx+1}. {step.get('component', 'Unknown Component')}**")
                st.markdown(step.get('description', ''))
                if step.get('file'):
                    st.markdown(f"*File: `{step.get('file')}`*")
                st.markdown("---")
            break

def _render_api_explorer(guide: OnboardingGuide):
    st.header("API Explorer")
    if not guide.api_explorer:
        st.info("No APIs documented.")
        return
        
    api_data = []
    for api in guide.api_explorer:
        api_data.append({
            "Method": api.method,
            "Path": api.path,
            "Purpose": api.purpose,
            "Handler": api.handler_function
        })
    st.dataframe(pd.DataFrame(api_data), hide_index=True)

def _render_reading_roadmap(guide: OnboardingGuide):
    st.header(f"Reading Roadmap ({guide.role.value})")
    for day in sorted(guide.reading_order, key=lambda x: x.day):
        with st.expander(f"Day {day.day}: {day.theme}", expanded=(day.day == 1)):
            st.markdown("**Topics:**")
            for topic in day.topics:
                st.markdown(f"- {topic}")
            st.markdown("**Files to read:**")
            for file in day.files:
                st.markdown(f"- `{file}`")

def _render_setup(guide: OnboardingGuide):
    st.header("Setup & Environment")
    
    st.subheader("Installation")
    for step in guide.setup_guide.installation_steps:
        st.markdown(f"- {step}")
        
    st.subheader("Environment Variables")
    if guide.setup_guide.environment_variables:
        st.dataframe(pd.DataFrame(guide.setup_guide.environment_variables), hide_index=True)
    else:
        st.write("None detected.")
        
    st.subheader("Commands")
    st.write("**Run Commands:**")
    for cmd in guide.setup_guide.run_commands:
        st.code(cmd.get("command", ""), language="bash")
        st.caption(cmd.get("description", ""))
        
    st.write("**Testing Commands:**")
    for cmd in guide.setup_guide.testing_commands:
        st.code(cmd, language="bash")
        
    if guide.setup_guide.docker_instructions:
        st.subheader("Docker Instructions")
        st.markdown(guide.setup_guide.docker_instructions)

def _render_gaps(guide: OnboardingGuide):
    st.header("Documentation Gaps")
    if not guide.documentation_gaps:
        st.success("No critical documentation gaps found!")
        return
        
    for gap in guide.documentation_gaps:
        color = "red" if gap.severity == "high" else "orange" if gap.severity == "medium" else "blue"
        st.markdown(f"### :{color}[{gap.gap_type}]")
        st.write(gap.description)
        if gap.affected_path:
            st.markdown(f"*Affected path: `{gap.affected_path}`*")
        st.divider()

def _render_confidence(guide: OnboardingGuide):
    st.header("Confidence Indicators")
    st.write("This shows the AI's confidence in the generated onboarding guide sections.")
    
    conf_data = []
    for ind in guide.confidence_indicators:
        conf_data.append({
            "Section": ind.section,
            "Confidence": f"{ind.confidence:.1%}",
            "Status": "✅ Solid" if ind.confidence > 0.8 else "⚠️ Needs Review" if ind.confidence > 0.4 else "❌ Unreliable"
        })
        
    st.table(pd.DataFrame(conf_data))
