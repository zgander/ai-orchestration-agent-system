from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel

from app.graph.state import InvestigationState
from app.graph.nodes import WorkflowNodes
from app.config.settings import Settings

def build_investigation_workflow(llm: BaseChatModel, settings: Settings):
    nodes = WorkflowNodes(llm, settings)
    
    workflow = StateGraph(InvestigationState)
    
    # Add nodes
    workflow.add_node("supervisor_node", nodes.supervisor_node)
    workflow.add_node("architecture_node", nodes.architecture_node)
    workflow.add_node("execution_flow_node", nodes.execution_flow_node)
    workflow.add_node("api_data_node", nodes.api_data_node)
    workflow.add_node("setup_node", nodes.setup_node)
    workflow.add_node("merge_results_node", nodes.merge_results_node)
    
    # Add edges
    workflow.add_edge(START, "supervisor_node")
    
    if settings.parallel_execution:
        # Fan out
        workflow.add_edge("supervisor_node", "architecture_node")
        workflow.add_edge("supervisor_node", "execution_flow_node")
        workflow.add_edge("supervisor_node", "api_data_node")
        workflow.add_edge("supervisor_node", "setup_node")
        
        # Fan in
        workflow.add_edge("architecture_node", "merge_results_node")
        workflow.add_edge("execution_flow_node", "merge_results_node")
        workflow.add_edge("api_data_node", "merge_results_node")
        workflow.add_edge("setup_node", "merge_results_node")
    else:
        # Sequential execution for easier debugging and cleaner timeline
        workflow.add_edge("supervisor_node", "architecture_node")
        workflow.add_edge("architecture_node", "execution_flow_node")
        workflow.add_edge("execution_flow_node", "api_data_node")
        workflow.add_edge("api_data_node", "setup_node")
        workflow.add_edge("setup_node", "merge_results_node")
        
    workflow.add_edge("merge_results_node", END)
    
    return workflow.compile()
