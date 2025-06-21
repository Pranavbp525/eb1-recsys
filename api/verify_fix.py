# verify_fix.py - Run this after applying the fix to verify it works

import asyncio
from nodes import generate_recommendations
from models import UserProfile, LawyerProfile

async def verify_fix():
    """Verify the generate_recommendations fix works."""
    
    print("🔧 Testing generate_recommendations fix...")
    print("=" * 50)
    
    # Create test state with mock data
    test_state = {
        "user_profile": UserProfile(
            name="Test User",
            occupation="Software Engineer", 
            industry="Technology",
            nationality="Indian",
            budget_range={"min": 15000, "max": 30000},
            location_preference="California",
            timeline_urgency="moderate",
            achievements=["Built AI system", "10 patents"],
            priority_factors=["success_rate", "cost"]
        ),
        "lawyer_profiles": [
            LawyerProfile(
                name="Sarah Johnson",
                firm="Tech Immigration Law",
                location="San Francisco, CA", 
                years_experience=15,
                eb1a_cases_handled=200,
                success_rate=94.5,
                specializations=["Technology", "AI/ML"],
                average_processing_time="8-10 months",
                fee_range={"min": 18000, "max": 25000},
                client_industries=["Tech", "Software"],
                notable_achievements=["Top EB-1A Attorney 2023"],
                contact_info={"email": "sarah@techimmlaw.com", "phone": "415-555-0123", "website": "www.techimmlaw.com"}
            ),
            LawyerProfile(
                name="Michael Chen",
                firm="Global Visa Partners",
                location="Los Angeles, CA",
                years_experience=12,
                eb1a_cases_handled=150,
                success_rate=91.0,
                specializations=["Engineering", "Research"],
                average_processing_time="10-12 months", 
                fee_range={"min": 15000, "max": 22000},
                client_industries=["Engineering", "Academia"],
                notable_achievements=["Published EB-1A Guide"],
                contact_info={"email": "mchen@gvp.com", "phone": "310-555-0456", "website": "www.gvp.com"}
            )
        ],
        "compatibility_scores": {
            "Sarah Johnson": 92.5,
            "Michael Chen": 85.0
        },
        "messages": []
    }
    
    try:
        # Run the function
        print("\n📊 Running generate_recommendations...")
        result = await generate_recommendations(test_state)
        
        # Check results
        print("\n✅ Function completed successfully!")
        print(f"\n📋 Recommendations generated: {len(result.get('recommendations', []))}")
        
        # Print recommendations
        for i, rec in enumerate(result.get('recommendations', [])):
            print(f"\n  Recommendation #{i+1}:")
            if isinstance(rec, dict) and 'lawyer' in rec:
                lawyer = rec['lawyer']
                print(f"    ✓ Lawyer: {lawyer.get('name', 'Unknown')}")
                print(f"    ✓ Firm: {lawyer.get('firm', 'Unknown')}")
                print(f"    ✓ Success Rate: {lawyer.get('success_rate', 'N/A')}%")
                print(f"    ✓ Compatibility: {rec.get('compatibility_score', 'N/A')}")
            else:
                print(f"    ❌ Invalid structure: {rec}")
        
        print(f"\n💭 Reasoning: {result.get('reasoning', 'No reasoning generated')}")
        
        # Check for errors
        if result.get('messages'):
            print(f"\n📝 Messages: {result['messages']}")
            
        print("\n✅ Fix verified! The function is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  The fix may not have been applied correctly.")

if __name__ == "__main__":
    asyncio.run(verify_fix())