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

class ReviewerAgent:
    def __init__(self, llm, settings: Settings):
        self.llm = llm
        self.settings = settings

    def review_finding(self, finding: AgentFinding, agent_type: AgentType) -> FindingReview:
        logger.info(f"Reviewing finding: '{finding.title}' from {agent_type.value}")
        
        # Check basic evidence requirement
        if self.settings.evidence_required and not finding.evidence:
            logger.info(f"Auto-rejecting finding '{finding.title}': No evidence provided.")
            return FindingReview(
                finding_title=finding.title,
                agent_type=agent_type,
                verdict=ReviewVerdict.REJECTED,
                confidence=1.0,
                reason="Auto-rejected: No evidence provided.",
                original_finding=finding
            )

        if finding.confidence < self.settings.min_confidence_threshold:
            logger.info(f"Auto-rejecting finding '{finding.title}': Confidence ({finding.confidence}) below threshold ({self.settings.min_confidence_threshold}).")
            return FindingReview(
                finding_title=finding.title,
                agent_type=agent_type,
                verdict=ReviewVerdict.REJECTED,
                confidence=1.0,
                reason=f"Auto-rejected: Confidence score {finding.confidence} is below minimum threshold {self.settings.min_confidence_threshold}.",
                original_finding=finding
            )

        finding_json = finding.model_dump_json()
        user_prompt = build_reviewer_prompt(finding_json, agent_type.value)
        
        try:
            structured_llm = self.llm.with_structured_output(ReviewerVerdictOutput)
            extraction_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
                ("human", "{text}")
            ])
            extractor = extraction_prompt | structured_llm
            
            result = extractor.invoke({"text": user_prompt})
            
            return FindingReview(
                finding_title=finding.title,
                agent_type=agent_type,
                verdict=result.verdict,
                confidence=result.confidence,
                reason=result.reason,
                original_finding=finding
            )
        except Exception as e:
            logger.error(f"Reviewer LLM failed for finding '{finding.title}': {e}")
            return FindingReview(
                finding_title=finding.title,
                agent_type=agent_type,
                verdict=ReviewVerdict.UNCERTAIN,
                confidence=0.0,
                reason=f"Review failed due to LLM error: {e}",
                original_finding=finding
            )

    def review_all_reports(self, agent_reports: Dict[AgentType, AgentReport]) -> ReviewReport:
        logger.info("Starting review of all agent reports...")
        
        reviews = []
        total_approved = 0
        total_rejected = 0
        total_uncertain = 0
        total_conf = 0.0
        
        for agent_type, report in agent_reports.items():
            if not report.findings:
                continue
                
            for finding in report.findings:
                review = self.review_finding(finding, agent_type)
                reviews.append(review)
                
                if review.verdict == ReviewVerdict.APPROVED:
                    total_approved += 1
                elif review.verdict == ReviewVerdict.REJECTED:
                    total_rejected += 1
                else:
                    total_uncertain += 1
                    
                total_conf += review.confidence
                
        overall_confidence = 0.0
        if reviews:
            overall_confidence = total_conf / len(reviews)
            
        return ReviewReport(
            reviews=reviews,
            total_approved=total_approved,
            total_rejected=total_rejected,
            total_uncertain=total_uncertain,
            overall_confidence=overall_confidence,
            revision_count=0,
            reviewed_at=datetime.now(timezone.utc)
        )
