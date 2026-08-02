import operator
from typing import TypedDict, List, Annotated, Optional
from app.models.chat_models import QueryClassification, ChatResponse, KnowledgeFragment
from app.models.investigation_models import AgentReport

class ChatTurnState(TypedDict):
    # Input
    user_message: str
    conversation_history: str       # Serialized previous messages
    repository_name: str
    repository_path: str
    analysis_result_json: str
    investigation_result_json: str
    
    # Processed
    query_classification: Optional[QueryClassification]
    knowledge_fragments: Annotated[List[KnowledgeFragment], operator.add]
    reinvestigation_result: Optional[AgentReport]
    
    # Output
    chat_response: Optional[ChatResponse]
    errors: Annotated[List[str], operator.add]
