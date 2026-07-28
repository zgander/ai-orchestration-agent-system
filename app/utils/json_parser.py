import re

def extract_json_from_llm(raw_text: str, expected_type: str = 'dict') -> str:
    """
    Sanitize LLM output and extract JSON string robustly.
    expected_type can be 'dict' (for {}) or 'list' (for []).
    """
    if not raw_text:
        return ""
        
    text = raw_text.strip()
    
    # Try finding markdown code block
    if expected_type == 'dict':
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    else:
        json_match = re.search(r'```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```', text, re.DOTALL)
        
    if json_match:
        return json_match.group(1).strip()
        
    # Fallback to finding first and last brackets
    start_char = '{' if expected_type == 'dict' else '['
    end_char = '}' if expected_type == 'dict' else ']'
    
    start = text.find(start_char)
    end = text.rfind(end_char)
    if start != -1 and end != -1:
        return text[start:end+1].strip()
        
    # If no brackets found, return as is (might just be raw JSON without markdown)
    return text.strip()
