from models import AgentState
from nodes import generate_search_queries, search_with_perplexity, extract_lawyer_profiles, calculate_compatibility, generate_recommendations
from langgraph.graph import StateGraph, END


# Build the Graph
def create_eb1a_agent():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate_queries", generate_search_queries)
    workflow.add_node("search_lawyers", search_with_perplexity)
    workflow.add_node("extract_profiles", extract_lawyer_profiles)
    workflow.add_node("calculate_compatibility", calculate_compatibility)
    workflow.add_node("generate_recommendations", generate_recommendations)
    
    # Define edges
    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "search_lawyers")
    workflow.add_edge("search_lawyers", "extract_profiles")
    workflow.add_edge("extract_profiles", "calculate_compatibility")
    workflow.add_edge("calculate_compatibility", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)
    
    return workflow.compile()

def create_eb1a_agent_dev():
    return create_eb1a_agent()

create_eb1a_agent_dev
