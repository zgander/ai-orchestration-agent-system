import streamlit as st
import pandas as pd

from app.models.review_models import ReviewReport, ReviewVerdict
from app.ui.components.evidence_viewer import render_evidence

def render_reviewer_dashboard(review_report: ReviewReport):
    st.header("🔍 Reviewer Dashboard")
    st.write("This dashboard shows the validation results of all findings produced by the specialist agents.")
    
    if not review_report:
        st.info("No review report available.")
        return

    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Findings", len(review_report.reviews))
    col2.metric("Approved", review_report.total_approved)
    col3.metric("Rejected", review_report.total_rejected)
    col4.metric("Overall Confidence", f"{review_report.overall_confidence:.1%}")
    
    st.divider()

    # Filter
    status_filter = st.selectbox(
        "Filter by Status", 
        ["All", ReviewVerdict.APPROVED.value, ReviewVerdict.REJECTED.value, ReviewVerdict.UNCERTAIN.value]
    )

    for review in review_report.reviews:
        if status_filter != "All" and review.verdict.value != status_filter:
            continue
            
        icon = "✅" if review.verdict == ReviewVerdict.APPROVED else "❌" if review.verdict == ReviewVerdict.REJECTED else "⚠️"
        
        with st.expander(f"{icon} {review.finding_title} ({review.agent_type.value})"):
            st.markdown(f"**Verdict:** {review.verdict.value}")
            st.markdown(f"**Reviewer Confidence:** {review.confidence:.1%}")
            st.markdown(f"**Reason:** {review.reason}")
            
            st.markdown("---")
            st.markdown(f"### Original Finding: {review.original_finding.title}")
            st.markdown(review.original_finding.description)
            st.markdown(f"**Agent Confidence:** {review.original_finding.confidence:.1%}")
            
            st.markdown("### Evidence")
            render_evidence(review.original_finding.evidence)
