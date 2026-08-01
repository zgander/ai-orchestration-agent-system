import json
from typing import Optional
from app.chat.conversation_memory import ConversationMemory
from app.graph.chat_workflow import build_chat_workflow
from app.models.chat_models import ChatMessage, ChatResponse, ChatSession
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatService:
    def __init__(self, llm, settings):
        self.llm = llm
        self.settings = settings
        self.memory = ConversationMemory(settings)
        self.workflow = build_chat_workflow(llm, settings)

    def ask(self, 
            message: str, 
            repository_name: str, 
            repository_path: str,
            analysis_result_json: str, 
            investigation_result_json: str, 
            session_id: Optional[str] = None) -> tuple[ChatResponse, ChatSession]:
            
        logger.info(f"Processing chat message for {repository_name} in session {session_id}")
        
        # Load or create session
        session = self.memory.get_or_create_session(session_id, repository_name)
        
        # Format history
        history_str = ""
        for msg in session.messages:
            history_str += f"{msg.role.upper()}: {msg.content}\n"
            
        if not history_str:
            history_str = "No previous messages."
            
        # Initialise state
        state = {
            "user_message": message,
            "conversation_history": history_str,
            "repository_name": repository_name,
            "repository_path": repository_path,
            "analysis_result_json": analysis_result_json,
            "investigation_result_json": investigation_result_json,
            "knowledge_fragments": [],
            "errors": []
        }
        
        # Run workflow
        result_state = self.workflow.invoke(state)
        
        # Extract response
        chat_response = result_state.get("chat_response")
        
        if not chat_response:
            # Fallback if graph failed
            from app.models.chat_models import ChatResponse as FallbackResponse
            chat_response = FallbackResponse(answer="I'm sorry, I encountered an internal error while processing your request.", citations=[], retrieved_sections=[], confidence=0.0)
            
        # Add messages to memory
        user_msg = ChatMessage(role="user", content=message)
        assistant_msg = ChatMessage(role="assistant", content=chat_response.answer, citations=chat_response.citations)
        
        updated_session = self.memory.add_messages(session, [user_msg, assistant_msg])
        
        return chat_response, updated_session

    def get_session_history(self, repository_name: str):
        return self.memory.get_session_history(repository_name)
