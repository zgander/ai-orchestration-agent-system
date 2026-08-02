
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.models.investigation_models import AgentType, AgentFinding
from app.models.analysis_models import AnalysisResult
from app.models.review_models import ReviewReport
from app.models.onboarding_models import (
    OnboardingGuide, OnboardingRole, RepositoryOverview, FolderExplanation,
    ImportantFile, ExecutionFlow, APIEndpointGuide, ReadingOrderDay,
    SetupGuide, ConfidenceIndicator, HealthScore, ArchitectureLayer, ComponentCard, DependencyInsight
)
from app.agents.prompts.synthesizer_prompt import (
    SYNTHESIZER_SYSTEM_PROMPT, build_overview_prompt, build_architecture_prompt,
    build_folder_guide_prompt, build_execution_flow_prompt,
    build_reading_order_prompt, build_setup_guide_prompt,
    build_mental_model_prompt, build_ai_insights_prompt, build_health_assessment_prompt,
    build_component_cards_prompt, build_architecture_layers_prompt
)
from app.analysis.gap_detector import GapDetector
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Structured Output Models for Sub-prompts
# These are intentionally kept FLAT and simple so that small LLMs (e.g. llama3.2:3b)
# can reliably produce valid JSON. Complex nested Pydantic schemas cause small models
# to hang or produce malformed output with structured_output.
from pydantic import BaseModel, Field

class OverviewOutput(BaseModel):
    description: str = Field(description="A short description of what this project does")
    languages: List[str] = Field(description="Programming languages used")
    frameworks: List[str] = Field(description="Frameworks used")
    architecture_style: str = Field(description="e.g. MVC, Microservices, Monolith")
    database: Optional[str] = Field(None, description="Database used, if any")
    testing_framework: Optional[str] = Field(None, description="Testing framework used, if any")
    project_type: str = Field(description="Type of project")
    primary_purpose: str = Field(description="Primary purpose of the project")
    main_components: List[str] = Field(description="List of main components")
    estimated_complexity: str = Field(description="Low, Medium, High")
    estimated_learning_time_minutes: int = Field(description="Estimated learning time in minutes")

class ArchitectureOutput(BaseModel):
    explanation: str = Field(description="High-level architecture explanation")
    diagram: Optional[str] = Field(None, description="Mermaid diagram string, if applicable")

class SimpleFolderEntry(BaseModel):
    path: str = Field(description="Folder path")
    purpose: str = Field(description="What this folder contains")
    importance: str = Field(description="high, medium, or low")
    read_first: bool = Field(description="Should a new dev read this first?")

class SimpleFileEntry(BaseModel):
    rank: int = Field(description="Importance rank (1 = most important)")
    file_path: str = Field(description="Path to the file")
    purpose: str = Field(description="What this file does")
    why_it_matters: str = Field(description="Why this file is important")

class FolderGuideOutput(BaseModel):
    folders: List[SimpleFolderEntry] = Field(description="Key folders in the project")
    important_files: List[SimpleFileEntry] = Field(description="Top 5 important files")

class SimpleFlowStep(BaseModel):
    step: str = Field(description="Step name")
    detail: str = Field(description="What happens in this step")

class SimpleExecutionFlow(BaseModel):
    name: str = Field(description="Name of this execution flow")
    steps: List[SimpleFlowStep] = Field(description="Steps in this flow")
    confidence: float = Field(description="Confidence from 0.0 to 1.0")
    supporting_files: List[str] = Field(description="Files supporting this flow")
    flow_type: str = Field(description="Startup | User Journey | Data Flow | Agent Collaboration")

class ExecutionFlowsOutput(BaseModel):
    flows: List[SimpleExecutionFlow] = Field(description="Execution flows in the application")

class MentalModelOutput(BaseModel):
    mental_model: str = Field(description="How to think about the repository organization")

class AIInsightsOutput(BaseModel):
    insights: List[str] = Field(description="Intelligent architectural and execution insights")

class HealthAssessmentOutput(BaseModel):
    health_scores: List[HealthScore] = Field(description="Repository health assessment scores")

class SimpleComponentCard(BaseModel):
    name: str = Field(description="Component name")
    purpose: str = Field(description="Component purpose")
    responsibilities: List[str] = Field(description="What this component is responsible for")
    consumes: List[str] = Field(description="What data or services it consumes")
    produces: List[str] = Field(description="What data or services it produces")
    dependencies: List[str] = Field(description="Other components it depends on")
    used_by: List[str] = Field(description="Other components that use this")

class ComponentCardsOutput(BaseModel):
    cards: List[SimpleComponentCard] = Field(description="Component architecture cards")

class SimpleArchitectureLayer(BaseModel):
    name: str = Field(description="Layer name")
    purpose: str = Field(description="Layer purpose")
    components: List[str] = Field(description="Components in this layer")
    order: int = Field(description="Layer order (1 = top/presentation layer)")

class ArchitectureLayersOutput(BaseModel):
    layers: List[SimpleArchitectureLayer] = Field(description="Logical architecture layers")

class SimpleReadingDay(BaseModel):
    day: int = Field(description="Day number")
    theme: str = Field(description="Theme for this day")
    topics: List[str] = Field(description="Topics to cover")
    files: List[str] = Field(description="Files to read")

class ReadingOrderOutput(BaseModel):
    days: List[SimpleReadingDay] = Field(description="Day-by-day reading order")

class SimpleSetupGuide(BaseModel):
    installation_steps: List[str] = Field(description="Steps to install the project")
    environment_variables: List[str] = Field(description="Required environment variable names")
    run_commands: List[str] = Field(description="Commands to run the project")
    testing_commands: List[str] = Field(description="Commands to run tests")

class SetupGuideOutput(BaseModel):
    setup: SimpleSetupGuide = Field(description="Setup guide for the project")


class SynthesizerAgent:
    # Per-extraction timeout in seconds
    EXTRACT_TIMEOUT_SECONDS = 300

    def __init__(self, llm, settings: Settings):
        self.llm = llm
        self.settings = settings
        self.gap_detector = GapDetector(settings)

    def _extract(self, prompt: str, output_model, step_name: str = ""):
        """Run a single structured LLM extraction with a timeout.

        Uses a background thread so that if the LLM hangs (common with
        small models + complex structured output), we don't block the
        entire synthesis pipeline forever.
        """
        label = step_name or output_model.__name__
        logger.info(f"[Synthesizer] Starting extraction: {label}")

        result_container = [None]
        error_container = [None]

        def _run():
            try:
                structured_llm = self.llm.with_structured_output(output_model)
                extraction_prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
                    ("human", "{text}")
                ])
                extractor = extraction_prompt | structured_llm
                result_container[0] = extractor.invoke({"text": prompt})
            except Exception as e:
                error_container[0] = e

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=self.EXTRACT_TIMEOUT_SECONDS)

        if thread.is_alive():
            logger.error(
                f"[Synthesizer] Extraction TIMED OUT after {self.EXTRACT_TIMEOUT_SECONDS}s: {label}. "
                f"The LLM may be struggling with the structured output schema. Skipping this section."
            )
            return None

        if error_container[0] is not None:
            logger.error(f"[Synthesizer] Extraction FAILED for {label}: {error_container[0]}")
            return None

        logger.info(f"[Synthesizer] Extraction completed: {label}")
        return result_container[0]

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

        from concurrent.futures import ThreadPoolExecutor
        
        overview_data = None
        arch_data = None
        folder_data = None
        exec_data = None
        reading_data = None
        setup_data = None
        mental_data = None
        insights_data = None
        health_data = None
        cards_data = None
        layers_data = None

        def extract_overview():
            nonlocal overview_data
            logger.info("[Synthesizer] Generating Overview...")
            overview_prompt = build_overview_prompt(
                findings=findings_text,
                analysis_data=analysis_result.model_dump_json(include={'tech_stack', 'statistics'}),
                role=role.value
            )
            overview_data = self._extract(overview_prompt, OverviewOutput, "Overview")

        def extract_architecture():
            nonlocal arch_data
            logger.info("[Synthesizer] Generating Architecture...")
            arch_prompt = build_architecture_prompt(findings_text, role.value)
            arch_data = self._extract(arch_prompt, ArchitectureOutput, "Architecture")

        def extract_folder_guide():
            nonlocal folder_data
            logger.info("[Synthesizer] Generating Folder Guide...")
            folder_prompt = build_folder_guide_prompt(
                findings=findings_text,
                analysis_data=analysis_result.tree.model_dump_json(include={'root'}),
                role=role.value
            )
            folder_data = self._extract(folder_prompt, FolderGuideOutput, "Folder Guide")
            
        def extract_execution_flows():
            nonlocal exec_data
            logger.info("[Synthesizer] Generating Execution Flows...")
            exec_prompt = build_execution_flow_prompt(findings_text, role.value)
            exec_data = self._extract(exec_prompt, ExecutionFlowsOutput, "Execution Flows")
            
        def extract_reading_order():
            nonlocal reading_data
            logger.info("[Synthesizer] Generating Reading Order...")
            reading_prompt = build_reading_order_prompt(findings_text, role.value)
            reading_data = self._extract(reading_prompt, ReadingOrderOutput, "Reading Order")
            
        def extract_setup_guide():
            nonlocal setup_data
            logger.info("[Synthesizer] Generating Setup Guide...")
            setup_prompt = build_setup_guide_prompt(
                findings=findings_text,
                analysis_data=analysis_result.model_dump_json(include={'env_variables'}),
                role=role.value
            )
            setup_data = self._extract(setup_prompt, SetupGuideOutput, "Setup Guide")

        def extract_mental_model():
            nonlocal mental_data
            logger.info("[Synthesizer] Generating Mental Model...")
            prompt = build_mental_model_prompt(findings_text, analysis_result.model_dump_json(include={'statistics'}))
            mental_data = self._extract(prompt, MentalModelOutput, "Mental Model")

        def extract_ai_insights():
            nonlocal insights_data
            logger.info("[Synthesizer] Generating AI Insights...")
            prompt = build_ai_insights_prompt(findings_text)
            insights_data = self._extract(prompt, AIInsightsOutput, "AI Insights")

        def extract_health_assessment():
            nonlocal health_data
            logger.info("[Synthesizer] Generating Health Assessment...")
            prompt = build_health_assessment_prompt(findings_text)
            health_data = self._extract(prompt, HealthAssessmentOutput, "Health Assessment")

        def extract_component_cards():
            nonlocal cards_data
            logger.info("[Synthesizer] Generating Component Cards...")
            prompt = build_component_cards_prompt(findings_text)
            cards_data = self._extract(prompt, ComponentCardsOutput, "Component Cards")

        def extract_architecture_layers():
            nonlocal layers_data
            logger.info("[Synthesizer] Generating Architecture Layers...")
            prompt = build_architecture_layers_prompt(findings_text)
            layers_data = self._extract(prompt, ArchitectureLayersOutput, "Architecture Layers")

        logger.info(f"Synthesizer running parallel extractions with {self.settings.max_parallel_agents} workers...")
        with ThreadPoolExecutor(max_workers=self.settings.max_parallel_agents) as executor:
            futures = [
                executor.submit(extract_overview),
                executor.submit(extract_architecture),
                executor.submit(extract_folder_guide),
                executor.submit(extract_execution_flows),
                executor.submit(extract_reading_order),
                executor.submit(extract_setup_guide),
                executor.submit(extract_mental_model),
                executor.submit(extract_ai_insights),
                executor.submit(extract_health_assessment),
                executor.submit(extract_component_cards),
                executor.submit(extract_architecture_layers),
            ]
            for future in futures:
                future.result()  # Wait for all to complete
                
        # 1. Overview
        repo_overview = RepositoryOverview(
            name=analysis_result.repository_info.name,
            description=overview_data.description if overview_data else "Failed to generate description.",
            languages=overview_data.languages if overview_data else [],
            frameworks=overview_data.frameworks if overview_data else [],
            architecture_style=overview_data.architecture_style if overview_data else "Unknown",
            database=overview_data.database if overview_data else None,
            testing_framework=overview_data.testing_framework if overview_data else None,
            project_type=overview_data.project_type if overview_data else "Unknown",
            primary_purpose=overview_data.primary_purpose if overview_data else "Unknown",
            main_components=overview_data.main_components if overview_data else [],
            estimated_complexity=overview_data.estimated_complexity if overview_data else "Unknown",
            estimated_learning_time_minutes=overview_data.estimated_learning_time_minutes if overview_data else 0,
            statistics=analysis_result.statistics.model_dump()
        )

        # 3. Folders and Files
        folder_guide = []
        if folder_data and folder_data.folders:
            for entry in folder_data.folders:
                folder_guide.append(FolderExplanation(
                    path=entry.path,
                    purpose=entry.purpose,
                    importance=entry.importance,
                    read_first=entry.read_first,
                    evidence=[]
                ))

        important_files = []
        if folder_data and folder_data.important_files:
            for entry in folder_data.important_files:
                important_files.append(ImportantFile(
                    rank=entry.rank,
                    file_path=entry.file_path,
                    purpose=entry.purpose,
                    why_it_matters=entry.why_it_matters,
                    dependencies=[],
                    evidence=[]
                ))

        # 4. Execution Flows
        execution_flows = []
        if exec_data and exec_data.flows:
            for flow in exec_data.flows:
                execution_flows.append(ExecutionFlow(
                    name=flow.name,
                    steps=[{"step": s.step, "detail": s.detail} for s in flow.steps],
                    evidence=[],
                    confidence=flow.confidence,
                    supporting_files=flow.supporting_files,
                    flow_type=flow.flow_type
                ))
        if not execution_flows:
            # Fallback if no flows
            execution_flows.append(ExecutionFlow(
                name="Fallback Startup Flow",
                steps=[{"step": "Start", "detail": "Application starts up based on entry points."}],
                evidence=[],
                confidence=0.1,
                supporting_files=[ep.file_path for ep in analysis_result.entry_points],
                flow_type="Startup"
            ))

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
        reading_order = []
        if reading_data and reading_data.days:
            for day in reading_data.days:
                reading_order.append(ReadingOrderDay(
                    day=day.day,
                    theme=day.theme,
                    topics=day.topics,
                    files=day.files
                ))

        # 7. Setup Guide
        setup_guide = SetupGuide(
            installation_steps=[], environment_variables=[], run_commands=[], testing_commands=[]
        )
        if setup_data and setup_data.setup:
            setup_guide = SetupGuide(
                installation_steps=setup_data.setup.installation_steps,
                environment_variables=[{"name": v} for v in setup_data.setup.environment_variables],
                run_commands=[{"command": c} for c in setup_data.setup.run_commands],
                testing_commands=setup_data.setup.testing_commands,
                evidence=[]
            )

        # 8. Documentation Gaps
        logger.info("[Synthesizer] Detecting documentation gaps...")
        gaps = self.gap_detector.detect(
            root_path=analysis_result.repository_info.root_path,
            analysis_result=analysis_result
        )

        # 9. Confidence Indicators
        conf_indicators = [
            ConfidenceIndicator(section="Overall Review", confidence=review_report.overall_confidence)
        ]

        # Assemble Final Guide
        logger.info("[Synthesizer] Assembling final onboarding guide...")
        
        # Clean up mermaid fences
        arch_diagram = arch_data.diagram if arch_data and self.settings.enable_mermaid_diagrams else None
        if arch_diagram:
            arch_diagram = arch_diagram.replace("```mermaid", "").replace("```", "").strip()

        return OnboardingGuide(
            role=role,
            repository_overview=repo_overview,
            architecture_explanation=arch_data.explanation if arch_data else "Failed to generate.",
            architecture_diagram=arch_diagram,
            folder_guide=folder_guide,
            important_files=important_files,
            execution_flows=execution_flows,
            api_explorer=api_guide,
            reading_order=reading_order,
            setup_guide=setup_guide,
            documentation_gaps=gaps,
            confidence_indicators=conf_indicators,
            mental_model=mental_data.mental_model if mental_data else repo_overview.description,
            ai_insights=insights_data.insights if insights_data else [],
            common_pitfalls=[gap.description for gap in gaps],
            repository_health=health_data.health_scores if health_data else [],
            architecture_layers=[
                ArchitectureLayer(
                    name=L.name, purpose=L.purpose, components=L.components, order=L.order
                ) for L in layers_data.layers
            ] if layers_data and layers_data.layers else [],
            component_cards=[
                ComponentCard(
                    name=C.name, purpose=C.purpose, responsibilities=C.responsibilities,
                    consumes=C.consumes, produces=C.produces, dependencies=C.dependencies,
                    used_by=C.used_by
                ) for C in cards_data.cards
            ] if cards_data and cards_data.cards else [],
            dependency_insights=[],
            generated_at=datetime.now(timezone.utc)
        )
