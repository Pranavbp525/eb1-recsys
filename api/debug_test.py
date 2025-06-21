# test_debug.py - Run this to debug your agent

import asyncio
import json
from models import UserProfile
from graph import create_eb1a_agent

async def test_agent_with_debug():
    """Test the agent with detailed debugging output."""
    
    # Create a test user
    test_user = UserProfile(
        name="Test User",
        occupation="Software Engineer",
        industry="Technology",
        nationality="Indian",
        budget_range={"min": 15000, "max": 30000},
        location_preference="California",
        timeline_urgency="moderate",
        achievements=[
            "Built AI system used by millions",
            "10 patents in machine learning",
            "Published 20 research papers"
        ],
        publications=20,
        citations=500,
        priority_factors=["success_rate", "industry_expertise"]
    )
    
    # Initialize state
    initial_state = {
        "user_profile": test_user,
        "search_queries": [],
        "raw_search_results": [],
        "lawyer_profiles": [],
        "compatibility_scores": {},
        "recommendations": [],
        "reasoning": "",
        "messages": []
    }
    
    print("🚀 Starting EB-1A Lawyer Agent Test")
    print("=" * 50)
    
    # Create agent
    agent = create_eb1a_agent()
    
    # Run agent with debugging
    try:
        print("\n📋 User Profile:")
        print(f"  Name: {test_user.name}")
        print(f"  Occupation: {test_user.occupation}")
        print(f"  Industry: {test_user.industry}")
        print(f"  Budget: ${test_user.budget_range['min']}-${test_user.budget_range['max']}")
        
        # Run the agent
        print("\n🔄 Running agent...")
        result = await agent.ainvoke(initial_state)
        
        # Debug output
        print("\n🔍 Agent Execution Summary:")
        print(f"  Search queries generated: {len(result.get('search_queries', []))}")
        if result.get('search_queries'):
            print("  Sample query:", result['search_queries'][0])
        
        print(f"\n  Search results: {len(result.get('raw_search_results', []))}")
        print(f"  Lawyer profiles extracted: {len(result.get('lawyer_profiles', []))}")
        
        if result.get('lawyer_profiles'):
            print("\n  Sample lawyer profile:")
            lawyer = result['lawyer_profiles'][0]
            print(f"    Name: {lawyer.name}")
            print(f"    Firm: {lawyer.firm}")
            print(f"    Success Rate: {lawyer.success_rate}%")
        
        print(f"\n  Compatibility scores calculated: {len(result.get('compatibility_scores', {}))}")
        if result.get('compatibility_scores'):
            print("  Scores:", json.dumps(result['compatibility_scores'], indent=2))
        
        print(f"\n  Recommendations generated: {len(result.get('recommendations', []))}")
        
        # Print recommendations
        if result.get('recommendations'):
            print("\n✅ Final Recommendations:")
            for i, rec in enumerate(result['recommendations']):
                print(f"\n  Recommendation #{i+1}:")
                
                # Safely access nested lawyer data
                if isinstance(rec, dict):
                    if 'lawyer' in rec and isinstance(rec['lawyer'], dict):
                        lawyer_info = rec['lawyer']
                        print(f"    Lawyer: {lawyer_info.get('name', 'Unknown')}")
                        print(f"    Firm: {lawyer_info.get('firm', 'Unknown')}")
                        print(f"    Success Rate: {lawyer_info.get('success_rate', 'N/A')}%")
                    else:
                        print(f"    ⚠️  Invalid lawyer data structure")
                        print(f"    Available keys: {list(rec.keys())}")
                    
                    print(f"    Compatibility Score: {rec.get('compatibility_score', 'N/A')}")
                    print(f"    Timeline: {rec.get('estimated_timeline', 'N/A')}")
                    print(f"    Cost: {rec.get('estimated_total_cost', 'N/A')}")
                else:
                    print(f"    ⚠️  Invalid recommendation format: {type(rec)}")
        else:
            print("\n❌ No recommendations generated")
        
        # Print reasoning
        if result.get('reasoning'):
            print(f"\n💭 Reasoning: {result['reasoning']}")
        
        # Print any error messages
        if result.get('messages'):
            print("\n📝 Process Messages:")
            for msg in result['messages']:
                print(f"  - {msg}")
                
    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Print state at failure
        print("\n🔍 State at failure:")
        for key in ['search_queries', 'raw_search_results', 'lawyer_profiles', 
                    'compatibility_scores', 'recommendations']:
            if key in result:
                print(f"  {key}: {len(result.get(key, [])) if isinstance(result.get(key), (list, dict)) else result.get(key)}")

if __name__ == "__main__":
    asyncio.run(test_agent_with_debug())