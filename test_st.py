import streamlit as st
import logging
from app.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("app.test")

st.write("Hello")
if st.button("Log"):
    with st.spinner("Logging..."):
        logger.info("THIS IS A TEST LOG FROM STREAMLIT")
