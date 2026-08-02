import streamlit as st
from app.config.settings import settings

def render_settings_page():
    st.title("⚙️ Settings")
    st.write("Configure application behavior and LLM preferences.")
    
    with st.form("settings_form"):
        st.subheader("LLM Provider")
        provider = st.selectbox("Provider", ["ollama", "openai", "anthropic"], index=["ollama", "openai", "anthropic"].index(settings.llm_provider))
        model = st.text_input("Model", value=settings.ollama_model)
        temperature = st.slider("Temperature", 0.0, 1.0, float(settings.temperature))
        
        st.subheader("Investigation")
        max_agents = st.number_input("Max Concurrent Agents", 1, 10, settings.max_parallel_agents)
        cache_hours = st.number_input("Cache TTL (hours)", 1, 168, settings.cache_max_age_hours)
        
        st.subheader("Export & Display")
        export_fmt = st.selectbox("Default Export Format", ["MARKDOWN", "JSON", "BUNDLE"], index=["MARKDOWN", "JSON", "BUNDLE"].index(settings.export_format))
        
        if st.form_submit_button("Save Settings", type="primary"):
            st.success("Settings saved successfully! (Note: changes are temporary in this demo unless written to .env)")
