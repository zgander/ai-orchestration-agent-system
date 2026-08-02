import streamlit as st
import pandas as pd

from app.models.review_models import ReviewReport, ReviewVerdict
from app.ui.components.evidence_viewer import render_evidence

def render_reviewer_dashboard(review_report: ReviewReport):
    st.header("🔍 Evidence & Verification")
    st.write("This dashboard shows the validation results of all findings produced by the specialist agents. Every claim must be backed by evidence.")
    
    if not review_report:
        st.info("No review report available.")
        return

    # Investigation Summary
    st.subheader("Investigation Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Findings", len(review_report.reviews))
    col2.metric("Verified (Approved)", review_report.total_approved)
    col3.metric("Needs Review (Rejected)", review_report.total_rejected)
    col4.metric("Overall Confidence", f"{review_report.overall_confidence:.1%}")
    
    st.divider()
    
    # Final Verdict
    st.markdown("### Final Verdict")
    if review_report.overall_confidence > 0.8 and review_report.total_rejected == 0:
        st.success("The repository has been thoroughly investigated and all findings are highly reliable.")
    elif review_report.overall_confidence > 0.6:
        st.warning("The investigation yielded mostly reliable results, but some findings lack strong evidence or contain contradictions.")
    else:
        st.error("The investigation results are unreliable. Please review the rejected findings and contradictions.")

    if hasattr(review_report, 'recommendations') and review_report.recommendations:
        st.markdown("**Reviewer Recommendations:**")
        for rec in review_report.recommendations:
            st.write(f"- {rec}")

    if hasattr(review_report, 'contradictions') and review_report.contradictions:
        st.divider()
        st.markdown("### ⚠️ Cross-Agent Contradictions")
        for contra in review_report.contradictions:
            st.error(f"**Contradiction Detected:** {contra}")
            
    st.divider()

    st.markdown("### Validation Matrix")
    
    matrix_data = []
    for review in review_report.reviews:
        matrix_data.append({
            "Finding": review.finding_title,
            "Produced By": review.agent_type.value,
            "Evidence Count": getattr(review, 'evidence_count', len(review.original_finding.evidence)),
            "Confidence": f"{review.confidence:.1%}",
            "Status": "Verified" if review.verdict == ReviewVerdict.APPROVED else "Needs Review"
        })
        
    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)
    
    st.divider()

    st.markdown("### Evidence View")
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
            
            # Confidence Breakdown
            st.markdown(f"**Reviewer Confidence:** {review.confidence:.1%}")
            # If we had a detailed breakdown, we would show it here.
            
            st.markdown(f"**Reason:** {review.reason}")
            
            st.markdown("---")
            st.markdown(f"### Original Claim: {review.original_finding.title}")
            st.markdown(review.original_finding.description)
            st.markdown(f"**Agent Confidence:** {review.original_finding.confidence:.1%}")
            
            st.markdown("### Evidence Supporting this Claim")
            if review.original_finding.evidence:
                render_evidence(review.original_finding.evidence)
            else:
                st.warning("No evidence provided for this claim.")
