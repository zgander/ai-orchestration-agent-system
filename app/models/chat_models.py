from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class CitationType(Enum):
    SECTION = "section"
    FILE = "file"
    FINDING = "finding"
    EVIDENCE = "evidence"

class Citation(BaseModel):
    type: CitationType
    reference: str
    display_text: str

class KnowledgeFragment(BaseModel):
    source_type: CitationType
    content: str
    relevance_score: float
    section_name: Optional[str] = None
    evidence: Optional[List[str]] = None

class QueryCategory(Enum):
    ARCHITECTURE = "architecture"
    EXECUTION_FLOW = "execution_flow"
    API = "api"
    SETUP = "setup"
    CODE = "code"
    GENERAL = "general"

class QueryClassification(BaseModel):
    category: QueryCategory
    sub_topics: List[str]
    requires_code_lookup: bool = False
    requires_reinvestigation: bool = False
    relevant_agents: List[str] = Field(default_factory=list)

class ChatMessage(BaseModel):
    role: str
    content: str
    citations: List[Citation] = Field(default_factory=list)

class ChatSession(BaseModel):
    session_id: str
    repository_name: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieved_sections: List[str]
    confidence: float
    required_reinvestigation: bool = False
