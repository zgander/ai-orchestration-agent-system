import streamlit as st
from typing import List
from app.models.analysis_models import APIEndpoint

def render_api_endpoints(endpoints: List[APIEndpoint]):
    if not endpoints:
        st.info("No API endpoints detected.")
        return
        
    st.markdown("### Detected API Routes")
    
    # Create HTML table
    html = """
    <table style="width: 100%; border-collapse: collapse; text-align: left;">
        <thead>
            <tr style="border-bottom: 1px solid #374151;">
                <th style="padding: 8px;">Method</th>
                <th style="padding: 8px;">Path</th>
                <th style="padding: 8px;">Framework</th>
                <th style="padding: 8px;">File</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for ep in endpoints:
        method_class = f"method-{ep.method}"
        html += f"""
        <tr style="border-bottom: 1px solid #1f2937;">
            <td style="padding: 8px;"><span class="method-badge {method_class}">{ep.method}</span></td>
            <td style="padding: 8px; font-family: monospace;">{ep.path}</td>
            <td style="padding: 8px; font-size: 0.9em;">{ep.framework}</td>
            <td style="padding: 8px; font-size: 0.8em; color: #9ca3af;">{ep.file_path}:{ep.line_number}</td>
        </tr>
        """
        
    html += """
        </tbody>
    </table>
    """
    
    st.markdown(html, unsafe_allow_html=True)
