from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from app.agents.prompts.chat_prompt import CHAT_SYSTEM_PROMPT, build_chat_user_prompt
from app.models.chat_models import ChatResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatAgent:
    def __init__(self, llm):
        self.llm = llm

    def generate_response(self, 
                          repository_name: str, 
                          condensed_overview: str, 
                          conversation_history: str, 
                          knowledge_fragments: str, 
                          user_message: str) -> str:
        logger.info("ChatAgent generating response...")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=CHAT_SYSTEM_PROMPT.format(
                repository_name=repository_name, 
                condensed_overview=condensed_overview
            )),
            HumanMessage(content=build_chat_user_prompt(
                conversation_history=conversation_history,
                knowledge_fragments=knowledge_fragments,
                user_message=user_message
            ))
        ])
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({})
            return result.content
        except Exception as e:
            logger.error(f"ChatAgent failed: {e}")
            return "I encountered an error while trying to answer your question. Please try again."
