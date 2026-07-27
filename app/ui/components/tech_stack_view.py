import streamlit as st
from app.models.analysis_models import TechStack, TechCategory

def render_tech_stack(tech_stack: TechStack):
    if not tech_stack.items:
        st.info("No specific technologies detected.")
        return
        
    categories = {
        TechCategory.LANGUAGE: "Languages",
        TechCategory.FRAMEWORK: "Frameworks",
        TechCategory.DATABASE: "Databases",
        TechCategory.PACKAGE_MANAGER: "Package Managers",
        TechCategory.TESTING: "Testing",
        TechCategory.CONTAINER: "Containers",
        TechCategory.CI_CD: "CI/CD"
    }
    
    # Group items by category
    grouped = {}
    for item in tech_stack.items:
        if item.category not in grouped:
            grouped[item.category] = []
        grouped[item.category].append(item)
        
    for cat in TechCategory:
        if cat in grouped:
            st.markdown(f"**{categories[cat]}**")
            
            html = ""
            # Sort by confidence descending
            items = sorted(grouped[cat], key=lambda x: x.confidence, reverse=True)
            for item in items:
                css_class = f"badge-{cat.value.lower()}"
                html += f'<span class="tech-badge {css_class}">{item.name}</span>'
            
            st.markdown(html, unsafe_allow_html=True)
            st.write("") # spacer
