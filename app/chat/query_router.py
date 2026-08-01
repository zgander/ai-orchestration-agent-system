from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.models.chat_models import QueryClassification, QueryCategory
from app.agents.prompts.query_router_prompt import QUERY_ROUTER_SYSTEM_PROMPT, build_query_router_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)

class QueryRouter:
    def __init__(self, llm):
        self.llm = llm

    def classify(self, query: str) -> QueryClassification:
        logger.info(f"Classifying query: '{query}'")
        try:
            structured_llm = self.llm.with_structured_output(QueryClassification)
            extraction_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=QUERY_ROUTER_SYSTEM_PROMPT),
                ("human", "{text}")
            ])
            extractor = extraction_prompt | structured_llm
            
            result = extractor.invoke({"text": build_query_router_prompt(query)})
            logger.info(f"Classification result: {result.category.value}")
            return result
        except Exception as e:
            logger.error(f"Failed to classify query: {e}. Falling back to GENERAL.")
            return QueryClassification(
                category=QueryCategory.GENERAL,
                sub_topics=[],
                requires_code_lookup=False,
                requires_reinvestigation=False,
                relevant_agents=[]
            )
