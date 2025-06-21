from models import UserProfile
from graph import create_eb1a_agent
import asyncio
import json
from datetime import datetime

async def find_eb1a_lawyers(user_profile: UserProfile):
    """Main function to find and recommend EB-1A lawyers."""
    
    # Initialize state
    initial_state = {
        "user_profile": user_profile,
        "search_queries": [],
        "raw_search_results": [],
        "lawyer_profiles": [],
        "compatibility_scores": {},
        "recommendations": [],
        "reasoning": "",
        "messages": []
    }
    
    # Create and run agent
    agent = create_eb1a_agent()
    
    # Execute the graph
    result = await agent.ainvoke(initial_state)
    
    # Format final output
    output = {
        "status": "success",
        "user": user_profile.name,
        "recommendations": result["recommendations"],
        "summary": result["reasoning"],
        "process_log": result["messages"],
        "timestamp": datetime.now().isoformat()
    }
    
    return output

# Example usage
if __name__ == "__main__":
    # Example user profile
    example_user = UserProfile(
        name="Dr. Rajesh Patel",
        occupation="AI Research Scientist",
        industry="Technology",
        nationality="Indian",
        budget_range={"min": 15000, "max": 30000},
        location_preference="California",
        timeline_urgency="moderate",
        achievements=[
            "Published 45 papers in top AI conferences",
            "Led team that developed breakthrough NLP model",
            "3 patents in machine learning",
            "Invited speaker at 10+ international conferences"
        ],
        publications=45,
        citations=1200,
        awards=["Best Paper Award NeurIPS 2023", "Google Research Award 2022"],
        priority_factors=["success_rate", "industry_expertise", "timeline"]
    )
    
    # Run the agent
    result = asyncio.run(find_eb1a_lawyers(example_user))
    print(json.dumps(result, indent=2))
