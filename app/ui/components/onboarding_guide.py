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
            "Overview & Mental Model",
            "Starting Point & Key Files",
            "Architecture & Flows",
            "API Explorer",
            "Learning Roadmap",
            "Setup & Environment",
            "Health & Pitfalls",
            "Documentation Gaps",
        ]
    )

    if section == "Overview & Mental Model":
        _render_overview(guide)
    elif section == "Starting Point & Key Files":
        _render_starting_point(guide)
    elif section == "Architecture & Flows":
        _render_architecture_and_flows(guide)
    elif section == "API Explorer":
        _render_api_explorer(guide)
    elif section == "Learning Roadmap":
        _render_reading_roadmap(guide)
    elif section == "Setup & Environment":
        _render_setup(guide)
    elif section == "Health & Pitfalls":
        _render_health_and_pitfalls(guide)
    elif section == "Documentation Gaps":
        _render_gaps(guide)

def _render_overview(guide: OnboardingGuide):
    st.header("Repository Overview")
    
    st.markdown("### Mental Model")
    st.info(guide.mental_model)
    
    st.markdown("### Repository at a Glance")
    ro = guide.repository_overview
    glance_data = {
        "Project Type": ro.project_type,
        "Primary Purpose": ro.primary_purpose,
        "Architecture": ro.architecture_style,
        "Complexity": ro.estimated_complexity,
        "Est. Learning Time": f"{ro.estimated_learning_time_minutes} minutes" if getattr(ro, 'estimated_learning_time_minutes', 0) > 0 else "Unknown",
        "Languages": ", ".join(ro.languages) if ro.languages else "N/A",
        "Frameworks": ", ".join(ro.frameworks) if ro.frameworks else "N/A"
    }
    
    df_glance = pd.DataFrame(list(glance_data.items()), columns=["Metric", "Value"])
    st.table(df_glance)

    if getattr(ro, 'main_components', None):
        st.markdown("**Main Components:**")
        for comp in ro.main_components:
            st.write(f"- {comp}")

    if hasattr(guide, 'ai_insights') and guide.ai_insights:
        st.divider()
        st.markdown("### 🤖 AI Insights")
        for insight in guide.ai_insights:
            st.write(f"- {insight}")

def _render_starting_point(guide: OnboardingGuide):
    st.header("Developer Starting Point")
    
    st.markdown("### Recommended First Files")
    if guide.important_files:
        for file in sorted(guide.important_files, key=lambda x: x.rank):
            with st.expander(f"#{file.rank} - 📄 {file.file_path}", expanded=(file.rank <= 3)):
                st.markdown(f"**Purpose:** {file.purpose}")
                st.markdown(f"**Why it matters:** {file.why_it_matters}")
                if getattr(file, 'dependencies', None):
                    st.markdown(f"**Dependencies:** {', '.join(file.dependencies)}")
                if file.evidence:
                     render_evidence(file.evidence, expandable=False)
    else:
        st.info("No important files ranked.")

    st.markdown("### Important Folders")
    for folder in guide.folder_guide:
        badge_color = "green" if folder.importance == "high" else "orange" if folder.importance == "medium" else "grey"
        read_badge = " **(Read First)**" if folder.read_first else ""
        
        with st.expander(f"📂 {folder.path} - :{badge_color}[{folder.importance.upper()}]{read_badge}"):
            st.markdown(folder.purpose)
            if folder.evidence:
                render_evidence(folder.evidence, expandable=False)

def _render_architecture_and_flows(guide: OnboardingGuide):
    st.header("Architecture & Flows")
    st.write("For an interactive exploration, please use the **Architecture Explorer** and **Execution Flow** pages.")
    
    if guide.architecture_diagram:
        st.subheader("Architecture Diagram")
        render_mermaid(guide.architecture_diagram)
    
    st.markdown(guide.architecture_explanation)

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
    st.header(f"Learning Roadmap ({guide.role.value})")
    
    if not guide.reading_order:
        st.info("No reading roadmap available.")
        return
        
    total_days = len(guide.reading_order)
    st.progress(0, text=f"0 / {total_days} Steps Completed")
    
    for day in sorted(guide.reading_order, key=lambda x: x.day):
        with st.expander(f"Step {day.day}: {day.theme}", expanded=(day.day == 1)):
            st.markdown("**Topics to learn:**")
            for topic in day.topics:
                st.markdown(f"- {topic}")
            st.markdown("**Files to read:**")
            for file in day.files:
                st.markdown(f"- `{file}`")

def _render_setup(guide: OnboardingGuide):
    st.header("Setup & Environment")
    
    st.subheader("Installation")
    if not guide.setup_guide.installation_steps:
        st.info("No installation steps detected.")
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
        
    if getattr(guide.setup_guide, 'docker_instructions', None):
        st.subheader("Docker Instructions")
        st.markdown(guide.setup_guide.docker_instructions)

def _render_health_and_pitfalls(guide: OnboardingGuide):
    st.header("Health & Pitfalls")
    
    if hasattr(guide, 'repository_health') and guide.repository_health:
        st.subheader("Repository Health")
        for score in guide.repository_health:
            icon = "✅" if score.score.lower() in ["good", "excellent", "high"] else "⚠️" if score.score.lower() in ["average", "medium", "fair"] else "❌"
            st.markdown(f"**{icon} {score.category}: {score.score}**")
            st.write(score.explanation)
    else:
        st.info("No health assessment available.")
        
    st.divider()
    
    if hasattr(guide, 'common_pitfalls') and guide.common_pitfalls:
        st.subheader("Common Pitfalls & Gotchas")
        for pitfall in guide.common_pitfalls:
            st.warning(pitfall)
    else:
        st.success("No common pitfalls identified.")

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
            
        st.markdown("**Recommended Action:** Address this gap to improve developer onboarding experience.")
        st.divider()
