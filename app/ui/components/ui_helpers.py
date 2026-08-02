import streamlit as st

def render_empty_state(icon: str, title: str, description: str, action_text: str = None, action_key: str = None) -> bool:
    """Renders a polished empty state with an optional action button."""
    st.markdown(f"""
    <div style='text-align: center; padding: 3rem; background-color: rgba(128,128,128,0.05); border-radius: 10px; margin: 2rem 0;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>{icon}</div>
        <h3 style='margin-bottom: 0.5rem;'>{title}</h3>
        <p style='color: #666;'>{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if action_text:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            return st.button(action_text, key=action_key, use_container_width=True, type="primary")
    return False

def render_metric_card(title: str, value: str, delta: str = None, icon: str = None):
    """Renders a styled metric card."""
    icon_html = f"<span style='font-size: 1.5rem; margin-right: 0.5rem;'>{icon}</span>" if icon else ""
    delta_html = f"<div style='color: {'#10b981' if delta.startswith('+') else '#ef4444'}; font-size: 0.875rem; margin-top: 0.5rem;'>{delta}</div>" if delta else ""
    
    st.markdown(f"""
    <div style='background-color: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.1); border-radius: 10px; padding: 1.5rem;'>
        <div style='display: flex; align-items: center; color: #666; margin-bottom: 0.5rem; font-weight: 500;'>
            {icon_html} {title}
        </div>
        <div style='font-size: 1.875rem; font-weight: 600; line-height: 1.2;'>
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
