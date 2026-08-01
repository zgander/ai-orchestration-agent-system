from typing import List
from app.models.chat_models import ChatResponse, Citation, KnowledgeFragment

class ResponseFormatter:
    def format_response(self, raw_answer: str, fragments: List[KnowledgeFragment], required_reinvestigation: bool = False) -> ChatResponse:
        citations = []
        retrieved_sections = []
        
        # Build citations mapping
        for idx, fragment in enumerate(fragments):
            citations.append(Citation(
                type=fragment.source_type,
                reference=fragment.section_name or f"fragment_{idx}",
                display_text=fragment.section_name or f"Source {idx+1}"
            ))
            if fragment.section_name and fragment.section_name not in retrieved_sections:
                retrieved_sections.append(fragment.section_name)
        
        # Replace inline citation markers [0], [1] with display text if needed
        # Or just pass the raw_answer and let the UI handle [0] -> Citation linking
        
        return ChatResponse(
            answer=raw_answer,
            citations=citations,
            retrieved_sections=retrieved_sections,
            confidence=1.0,
            required_reinvestigation=required_reinvestigation
        )
