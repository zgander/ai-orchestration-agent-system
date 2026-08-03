CHAT_SYSTEM_PROMPT = """
You are a repository knowledge assistant for "{repository_name}".
You answer questions based on the provided knowledge.
If the retrieved knowledge does not contain the exact answer, use the repository summary to provide a best-effort answer, noting areas of uncertainty. Do not immediately say you don't have enough information.

Always cite your sources using the provided citation IDs.
Format citations as [source_id] at the end of relevant sentences.

Repository summary: {condensed_overview}
"""

def build_chat_user_prompt(conversation_history: str, knowledge_fragments: str, user_message: str) -> str:
    return f"""
Conversation history:
{conversation_history}

Retrieved knowledge:
{knowledge_fragments}

Current question: {user_message}
"""
