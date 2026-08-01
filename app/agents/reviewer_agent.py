from typing import Dict, List, Any
from datetime import datetime, timezone
import json

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.models.investigation_models import AgentType, AgentReport, AgentFinding
from app.models.review_models import ReviewReport, FindingReview, ReviewVerdict
from app.agents.prompts.reviewer_prompt import REVIEWER_SYSTEM_PROMPT, build_reviewer_prompt
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ReviewerVerdictOutput(BaseModel):
    verdict: ReviewVerdict = Field(description="APPROVED or REJECTED")
    reason: str = Field(description="Reason for the verdict")
    confidence: float = Field(description="Confidence in this review (0.0 to 1.0)")

class ReviewerBatchOutput(BaseModel):
    reviews: List[ReviewerVerdictOutput] = Field(description="List of reviews corresponding to the findings")

class ReviewerAgent:
    def __init__(self, llm, settings: Settings):
        self.llm = llm
        self.settings = settings

    def review_findings_batch(self, findings: List[tuple[AgentType, AgentFinding]]) -> List[FindingReview]:
        logger.info(f"Reviewing {len(findings)} findings in a batch...")
        
        # Pre-filter findings that obviously fail thresholds
        valid_findings = []
        auto_reviews = []
        
        for i, (agent_type, finding) in enumerate(findings):
            if self.settings.evidence_required and not finding.evidence:
                logger.info(f"Auto-rejecting finding '{finding.title}': No evidence provided.")
                auto_reviews.append((i, FindingReview(
                    finding_title=finding.title,
                    agent_type=agent_type,
                    verdict=ReviewVerdict.REJECTED,
                    confidence=1.0,
                    reason="Auto-rejected: No evidence provided.",
                    original_finding=finding
                )))
                continue

            if finding.confidence < self.settings.min_confidence_threshold:
                logger.info(f"Auto-rejecting finding '{finding.title}': Confidence ({finding.confidence}) below threshold ({self.settings.min_confidence_threshold}).")
                auto_reviews.append((i, FindingReview(
                    finding_title=finding.title,
                    agent_type=agent_type,
                    verdict=ReviewVerdict.REJECTED,
                    confidence=1.0,
                    reason=f"Auto-rejected: Confidence score {finding.confidence} is below minimum threshold.",
                    original_finding=finding
                )))
                continue
                
            valid_findings.append((i, agent_type, finding))
            
        if not valid_findings:
            return [r for _, r in sorted(auto_reviews)]

        # Prepare batch prompt
        from app.agents.prompts.reviewer_prompt import build_reviewer_batch_prompt
        
        findings_data = []
        for _, agent_type, finding in valid_findings:
            findings_data.append({
                "agent": agent_type.value,
                "finding": finding.model_dump()
            })
            
        user_prompt = build_reviewer_batch_prompt(json.dumps(findings_data, indent=2))
        
        try:
            structured_llm = self.llm.with_structured_output(ReviewerBatchOutput)
            extraction_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
                ("human", "{text}")
            ])
            extractor = extraction_prompt | structured_llm
            
            result = extractor.invoke({"text": user_prompt})
            
            # Map back to valid findings
            llm_reviews = []
            if result and result.reviews and len(result.reviews) == len(valid_findings):
                for (orig_idx, agent_type, finding), llm_review in zip(valid_findings, result.reviews):
                    llm_reviews.append((orig_idx, FindingReview(
                        finding_title=finding.title,
                        agent_type=agent_type,
                        verdict=llm_review.verdict,
                        confidence=llm_review.confidence,
                        reason=llm_review.reason,
                        original_finding=finding
                    )))
            else:
                logger.warning("Batch review returned mismatched length. Falling back to UNCERTAIN.")
                for orig_idx, agent_type, finding in valid_findings:
                    llm_reviews.append((orig_idx, FindingReview(
                        finding_title=finding.title,
                        agent_type=agent_type,
                        verdict=ReviewVerdict.UNCERTAIN,
                        confidence=0.0,
                        reason="Batch review mismatch",
                        original_finding=finding
                    )))
                    
        except Exception as e:
            logger.error(f"Batch Reviewer LLM failed: {e}")
            llm_reviews = []
            for orig_idx, agent_type, finding in valid_findings:
                llm_reviews.append((orig_idx, FindingReview(
                    finding_title=finding.title,
                    agent_type=agent_type,
                    verdict=ReviewVerdict.UNCERTAIN,
                    confidence=0.0,
                    reason=f"LLM error: {e}",
                    original_finding=finding
                )))
                
        # Recombine and sort by original index
        all_reviews = auto_reviews + llm_reviews
        all_reviews.sort(key=lambda x: x[0])
        return [r for _, r in all_reviews]

    def review_all_reports(self, agent_reports: Dict[AgentType, AgentReport]) -> ReviewReport:
        logger.info("Starting review of all agent reports...")
        
        all_findings = []
        for agent_type, report in agent_reports.items():
            if report.findings:
                for finding in report.findings:
                    all_findings.append((agent_type, finding))
                    
        if not all_findings:
            return ReviewReport(
                reviews=[],
                total_approved=0,
                total_rejected=0,
                total_uncertain=0,
                overall_confidence=0.0,
                revision_count=0,
                reviewed_at=datetime.now(timezone.utc)
            )
            
        # Batch review
        reviews = self.review_findings_batch(all_findings)
        
        total_approved = sum(1 for r in reviews if r.verdict == ReviewVerdict.APPROVED)
        total_rejected = sum(1 for r in reviews if r.verdict == ReviewVerdict.REJECTED)
        total_uncertain = sum(1 for r in reviews if r.verdict == ReviewVerdict.UNCERTAIN)
        total_conf = sum(r.confidence for r in reviews)
                
        overall_confidence = total_conf / len(reviews) if reviews else 0.0
            
        return ReviewReport(
            reviews=reviews,
            total_approved=total_approved,
            total_rejected=total_rejected,
            total_uncertain=total_uncertain,
            overall_confidence=overall_confidence,
            revision_count=0,
            reviewed_at=datetime.now(timezone.utc)
        )
