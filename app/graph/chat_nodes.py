import json
from app.graph.chat_state import ChatTurnState
from app.chat.query_router import QueryRouter
from app.chat.knowledge_retriever import KnowledgeRetriever
from app.chat.response_formatter import ResponseFormatter
from app.agents.chat_agent import ChatAgent
from app.chat.reinvestigation_service import ReInvestigationService
from app.models.analysis_models import AnalysisResult
from app.models.investigation_models import InvestigationResult
from app.agents.prompts.prompt_utils import build_condensed_context
from app.models.investigation_models import AgentType
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatWorkflowNodes:
    def __init__(self, llm, settings):
        self.settings = settings
        self.query_router = QueryRouter(llm)
        self.knowledge_retriever = KnowledgeRetriever(max_fragments=settings.max_knowledge_fragments)
        self.chat_agent = ChatAgent(llm)
        self.response_formatter = ResponseFormatter()
        self.reinvestigation_service = ReInvestigationService(llm, settings)

    def classify_query(self, state: ChatTurnState):
        logger.info("Node: classify_query")
        classification = self.query_router.classify(state["user_message"])
        return {"query_classification": classification}

    def retrieve_knowledge(self, state: ChatTurnState):
        logger.info("Node: retrieve_knowledge")
        try:
            analysis = AnalysisResult.model_validate_json(state["analysis_result_json"])
            investigation = InvestigationResult.model_validate_json(state["investigation_result_json"])
            
            fragments = self.knowledge_retriever.retrieve(
                query=state["user_message"],
                classification=state["query_classification"],
                analysis_result=analysis,
                investigation_result=investigation
            )
            return {"knowledge_fragments": fragments}
        except Exception as e:
            logger.error(f"Retrieve knowledge failed: {e}")
            return {"errors": [f"Retrieve failed: {str(e)}"], "knowledge_fragments": []}

    def should_reinvestigate(self, state: ChatTurnState) -> str:
        fragments = state.get("knowledge_fragments", [])
        classification = state.get("query_classification")
        
        # If we have a high relevance fragment, don't reinvestigate
        if fragments and any(f.relevance_score > 0.5 for f in fragments):
            return "generate_response"
            
        if self.settings.enable_reinvestigation and classification and classification.requires_reinvestigation:
            return "reinvestigate"
            
        return "generate_response"

    def reinvestigate(self, state: ChatTurnState):
        logger.info("Node: reinvestigate")
        try:
            report = self.reinvestigation_service.run(
                repository_path=state["repository_path"],
                query=state["user_message"],
                classification=state["query_classification"],
                analysis_result_json=state["analysis_result_json"]
            )
            return {"reinvestigation_result": report}
        except Exception as e:
            logger.error(f"Reinvestigation failed: {e}")
            return {"errors": [f"Reinvestigation failed: {str(e)}"]}

    def generate_response(self, state: ChatTurnState):
        logger.info("Node: generate_response")
        fragments = state.get("knowledge_fragments", [])
        
        # If we reinvestigated, add those findings to fragments
        report = state.get("reinvestigation_result")
        required_reinvestigation = False
        if report and report.findings:
            required_reinvestigation = True
            from app.models.chat_models import KnowledgeFragment, CitationType
            for finding in report.findings:
                fragments.append(KnowledgeFragment(
                    source_type=CitationType.FINDING,
                    content=f"New Finding: {finding.title}\n{finding.description}",
                    relevance_score=1.0,
                    section_name=f"New: {finding.title}",
                    evidence=[e.content for e in finding.evidence] if finding.evidence else None
                ))
        
        # Serialize fragments for the prompt
        fragments_str = ""
        for i, f in enumerate(fragments):
            fragments_str += f"[{i}] {f.source_type.value} ({f.section_name}):\n{f.content}\n\n"
            
        if not fragments_str:
            fragments_str = "No relevant knowledge found."
            
        condensed_overview = build_condensed_context(state["analysis_result_json"], AgentType.ARCHITECTURE)

        raw_answer = self.chat_agent.generate_response(
            repository_name=state["repository_name"],
            condensed_overview=condensed_overview,
            conversation_history=state["conversation_history"],
            knowledge_fragments=fragments_str,
            user_message=state["user_message"]
        )
        
        chat_response = self.response_formatter.format_response(
            raw_answer=raw_answer,
            fragments=fragments,
            required_reinvestigation=required_reinvestigation
        )
        
        return {"chat_response": chat_response}
