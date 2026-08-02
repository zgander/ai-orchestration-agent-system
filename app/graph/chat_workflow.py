from langgraph.graph import StateGraph, START, END
from app.graph.chat_state import ChatTurnState
from app.graph.chat_nodes import ChatWorkflowNodes

def build_chat_workflow(llm, settings):
    nodes = ChatWorkflowNodes(llm, settings)
    workflow = StateGraph(ChatTurnState)

    workflow.add_node("classify_query", nodes.classify_query)
    workflow.add_node("retrieve_knowledge", nodes.retrieve_knowledge)
    workflow.add_node("reinvestigate", nodes.reinvestigate)
    workflow.add_node("generate_response", nodes.generate_response)

    workflow.add_edge(START, "classify_query")
    workflow.add_edge("classify_query", "retrieve_knowledge")

    workflow.add_conditional_edges(
        "retrieve_knowledge",
        nodes.should_reinvestigate,
        {"reinvestigate": "reinvestigate", "generate_response": "generate_response"}
    )
    workflow.add_edge("reinvestigate", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()
