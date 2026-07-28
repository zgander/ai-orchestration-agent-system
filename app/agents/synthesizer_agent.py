import json
from datetime import datetime, timezone
from typing import Dict, List, Any

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.models.investigation_models import AgentType, AgentFinding
from app.models.analysis_models import AnalysisResult
from app.models.review_models import ReviewReport
from app.models.onboarding_models import (
    OnboardingGuide, OnboardingRole, RepositoryOverview, FolderExplanation,
    ImportantFile, ExecutionFlow, APIEndpointGuide, ReadingOrderDay,
    SetupGuide, ConfidenceIndicator
)
from app.agents.prompts.synthesizer_prompt import (
    SYNTHESIZER_SYSTEM_PROMPT, build_overview_prompt, build_architecture_prompt,
    build_folder_guide_prompt, build_execution_flow_prompt,
    build_reading_order_prompt, build_setup_guide_prompt
)
from app.analysis.gap_detector import GapDetector
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Structured Output Models for Sub-prompts
from pydantic import BaseModel, Field

class OverviewOutput(BaseModel):
    description: str
    languages: List[str]
    frameworks: List[str]
    architecture_style: str
    database: str = None
    testing_framework: str = None

class ArchitectureOutput(BaseModel):
    explanation: str
    diagram: str = None

class FolderGuideOutput(BaseModel):
    folders: List[FolderExplanation]
    important_files: List[ImportantFile]

class ExecutionFlowsOutput(BaseModel):
    flows: List[ExecutionFlow]

class ReadingOrderOutput(BaseModel):
    days: List[ReadingOrderDay]

class SetupGuideOutput(BaseModel):
    setup: SetupGuide


class SynthesizerAgent:
    def __init__(self, llm, settings: Settings):
        self.llm = llm
        self.settings = settings
        self.gap_detector = GapDetector(settings)

    def _extract(self, prompt: str, output_model):
        try:
            structured_llm = self.llm.with_structured_output(output_model)
            extraction_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
                ("human", "{text}")
            ])
            extractor = extraction_prompt | structured_llm
            return extractor.invoke({"text": prompt})
        except Exception as e:
            logger.error(f"Synthesis extraction failed for {output_model.__name__}: {e}")
            return None

    def synthesize(
        self,
        approved_findings: Dict[AgentType, List[AgentFinding]],
        review_report: ReviewReport,
        analysis_result: AnalysisResult,
        role: OnboardingRole
    ) -> OnboardingGuide:
        logger.info(f"Synthesizer generating onboarding guide for {role.value}")
        
        # Format findings for prompt
        findings_text = ""
        for agent_type, findings in approved_findings.items():
            findings_text += f"\n--- {agent_type.value} ---\n"
            for f in findings:
                findings_text += f"Title: {f.title}\nDescription: {f.description}\n\n"

        # 1. Overview
        overview_prompt = build_overview_prompt(
            findings=findings_text,
            analysis_data=analysis_result.model_dump_json(include={'tech_stack', 'statistics'}),
            role=role.value
        )
        overview_data = self._extract(overview_prompt, OverviewOutput)
        
        repo_overview = RepositoryOverview(
            name=analysis_result.repository_info.name,
            description=overview_data.description if overview_data else "Failed to generate description.",
            languages=overview_data.languages if overview_data else [],
            frameworks=overview_data.frameworks if overview_data else [],
            architecture_style=overview_data.architecture_style if overview_data else "Unknown",
            database=overview_data.database if overview_data else None,
            testing_framework=overview_data.testing_framework if overview_data else None,
            statistics=analysis_result.statistics.model_dump()
        )

        # 2. Architecture
        arch_prompt = build_architecture_prompt(findings_text, role.value)
        arch_data = self._extract(arch_prompt, ArchitectureOutput)

        # 3. Folders and Files
        folder_prompt = build_folder_guide_prompt(
            findings=findings_text,
            analysis_data=analysis_result.tree.model_dump_json(include={'root'}),
            role=role.value
        )
        folder_data = self._extract(folder_prompt, FolderGuideOutput)

        # 4. Execution Flows
        exec_prompt = build_execution_flow_prompt(findings_text, role.value)
        exec_data = self._extract(exec_prompt, ExecutionFlowsOutput)

        # 5. API Explorer (Deterministic from AnalysisResult + Findings)
        # LLM extraction for this is often lossy, so we combine deterministically
        api_guide = []
        for api in analysis_result.api_endpoints:
            api_guide.append(APIEndpointGuide(
                method=api.method,
                path=api.path,
                purpose=f"Endpoint handled by {api.handler_name}",
                handler_file=api.file_path,
                handler_function=api.handler_name,
                evidence=[]
            ))

        # 6. Reading Order
        reading_prompt = build_reading_order_prompt(findings_text, role.value)
        reading_data = self._extract(reading_prompt, ReadingOrderOutput)

        # 7. Setup Guide
        setup_prompt = build_setup_guide_prompt(
            findings=findings_text,
            analysis_data=analysis_result.model_dump_json(include={'env_variables'}),
            role=role.value
        )
        setup_data = self._extract(setup_prompt, SetupGuideOutput)

        # 8. Documentation Gaps
        gaps = self.gap_detector.detect(
            root_path=analysis_result.repository_info.root_path,
            analysis_result=analysis_result
        )

        # 9. Confidence Indicators
        conf_indicators = [
            ConfidenceIndicator(section="Overall Review", confidence=review_report.overall_confidence)
        ]

        # Assemble Final Guide
        return OnboardingGuide(
            role=role,
            repository_overview=repo_overview,
            architecture_explanation=arch_data.explanation if arch_data else "Failed to generate.",
            architecture_diagram=arch_data.diagram if arch_data and self.settings.enable_mermaid_diagrams else None,
            folder_guide=folder_data.folders if folder_data else [],
            important_files=folder_data.important_files if folder_data else [],
            execution_flows=exec_data.flows if exec_data else [],
            api_explorer=api_guide,
            reading_order=reading_data.days if reading_data else [],
            setup_guide=setup_data.setup if setup_data else SetupGuide(
                installation_steps=[], environment_variables=[], run_commands=[], testing_commands=[]
            ),
            documentation_gaps=gaps,
            confidence_indicators=conf_indicators,
            mental_model=repo_overview.description,
            generated_at=datetime.now(timezone.utc)
        )
