from models import AgentState, LawyerProfile, UserProfile
from prompts import LAWYER_FINDER_AGENT_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# LLM for Perplexity Search
# Print API keys to check if they are loaded
perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
openrouter_key = os.environ.get("OPENROUTER_API_KEY")

# print(f"Perplexity API Key loaded: {perplexity_key}")
# print(f"OpenRouter API Key loaded: {openrouter_key}")

perplexity_llm = ChatOpenAI(
    model="sonar",
    api_key=perplexity_key,
    base_url="https://api.perplexity.ai"
)

# LLM for other tasks (generation, extraction, scoring)
openrouter_llm = ChatOpenAI(
    model="mistralai/mistral-small-3.2-24b-instruct:free",
    # model="deepseek/deepseek-chat-v3-0324:free",
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1"
)

async def generate_search_queries(state: AgentState) -> AgentState:
    """Generate targeted search queries based on user profile."""

    user_profile = state["user_profile"]

    search_prompt = f"""
    You are an expert at crafting search queries for finding EB-1A immigration lawyers.

    User Profile:
    - Occupation: {user_profile.occupation}
    - Industry: {user_profile.industry}
    - Nationality: {user_profile.nationality}
    - Location Preference: {user_profile.location_preference or 'Any'}
    - Budget: ${user_profile.budget_range['min']} - ${user_profile.budget_range['max']}
    - Timeline: {user_profile.timeline_urgency}
    - Key Achievements: {', '.join(user_profile.achievements[:3])}

    Generate 5 specific search queries for Perplexity API that will find:
    1. EB-1A lawyers with high success rates (90%+)
    2. Lawyers experienced with {user_profile.nationality} nationals
    3. Lawyers specializing in {user_profile.industry}
    4. Location-specific lawyers if applicable
    5. Lawyers within the budget range

    Format your response as a JSON array of search queries.
    Focus on finding lawyers with verifiable success rates and specific EB-1A experience.
    """

    response = await openrouter_llm.ainvoke([
        SystemMessage(content="You are an expert at generating search queries for finding specialized lawyers."),
        HumanMessage(content=search_prompt)
    ])

    # Parse the queries from LLM response
    import re
    queries_text = response.content

    # Extract JSON array from response
    json_match = re.search(r'\[.*\]', queries_text, re.DOTALL)
    if json_match:
        queries = json.loads(json_match.group())
    else:
        # Fallback queries
        queries = [
            f"EB-1A immigration lawyers 90% success rate {user_profile.industry}",
            f"Top EB-1A attorneys {user_profile.nationality} extraordinary ability visa",
            f"Best EB-1A lawyers high approval rate {user_profile.location_preference or 'USA'}",
            f"Immigration lawyers EB-1A {user_profile.occupation} cases statistics",
            "EB-1A visa attorneys success rate data verified results"
        ]

    state["search_queries"] = queries
    state["messages"].append(f"Generated {len(queries)} search queries")
    return state

# Node 2: Execute Perplexity Search
async def search_with_perplexity(state: AgentState) -> AgentState:
    """Execute searches using Perplexity API."""

    all_results = []

    for query in state["search_queries"]:
        perplexity_prompt = f"""
        Search for information about EB-1A immigration lawyers with the following query:
        "{query}"

        Focus on finding:
        - Lawyer names and firms
        - Contact information
        - Client testimonials

        Provide detailed, factual information with sources when available.
        """

        try:
            response = await perplexity_llm.ainvoke([
                SystemMessage(content="You are a helpful assistant finding information about immigration lawyers."),
                HumanMessage(content=perplexity_prompt)
            ])

            all_results.append({
                "query": query,
                "results": response.content
            })

        except Exception as e:
            state["messages"].append(f"Error searching with Perplexity: {str(e)}")
            # Fallback to regular LLM with mock data
            all_results.append({
                "query": query,
                "results": f"Mock search results for: {query}"
            })

    state["raw_search_results"] = all_results
    state["messages"].append(f"Completed {len(all_results)} searches")
    return state

# Node 3: Extract and Generate Lawyer Profiles
async def extract_lawyer_profiles(state: AgentState) -> AgentState:
    """Extract structured lawyer profiles from search results."""

    extraction_prompt = f"""
    You are an expert at extracting structured information about lawyers from search results.

    Search Results:
    {json.dumps(state["raw_search_results"], indent=2)}

    Extract information about EB-1A immigration lawyers and create detailed profiles.

    For each lawyer found, extract:
    - Full name
    - Law firm
    - Contact information (email, phone, website)

    IMPORTANT RULES:
    1. Verify the lawyer specializes in EB-1A specifically, not just general immigration.
    2. Only include lawyers where you can find contact information.

    Return the profiles as a JSON array. Each profile should match this structure:
    {{
        "name": "string",
        "firm": "string",
        "contact_info": {{"email": "string", "phone": "string", "website": "string"}}
    }}
    """

    response = await openrouter_llm.ainvoke([
        SystemMessage(content="You are an expert at extracting and structuring lawyer information from text."),
        HumanMessage(content=extraction_prompt)
    ])

    # Parse lawyer profiles
    profiles_text = response.content
    json_match = re.search(r'\[.*\]', profiles_text, re.DOTALL)

    if json_match:
        try:
            profiles_data = json.loads(json_match.group())
            lawyer_profiles = [LawyerProfile(**profile) for profile in profiles_data]
        except (json.JSONDecodeError, TypeError) as e:
            state["messages"].append(f"Error parsing lawyer profiles: {str(e)}. No profiles extracted.")
            lawyer_profiles = []
    else:
        # Fallback with no profiles if no JSON is found
        state["messages"].append("Could not find any lawyer profiles in the search results.")
        lawyer_profiles = []

    state["lawyer_profiles"] = lawyer_profiles
    state["messages"].append(f"Extracted {len(lawyer_profiles)} qualified lawyer profiles")
    return state

# Node 5: Generate Final Recommendations
async def generate_recommendations(state: AgentState) -> AgentState:
    """Generate final lawyer recommendations."""

    user_profile = state["user_profile"]

    recommendation_prompt = f"""
    You are an expert at making personalized lawyer recommendations for EB-1A visa applications.

    User Profile:
    {user_profile.model_dump_json(indent=2)}

    Lawyer Profiles:
    {json.dumps([lawyer.model_dump() for lawyer in state["lawyer_profiles"]], indent=2)}

    Based on the available information, recommend the TOP 2 lawyers for this user.

    Your response MUST be a single, valid JSON array. Each object in the array represents one
    lawyer recommendation and MUST conform to the exact structure below. Do not add any
    introductory text or explanations outside of the JSON structure.

    ```json
    [
      {{
        "lawyer": {{
          "name": "Lawyer's Full Name",
          "firm": "Name of the Law Firm",
          "contact_info": {{
            "email": "lawyer@example.com",
            "phone": "123-456-7890",
            "website": "[www.lawfirm.com](https://www.lawfirm.com)"
          }}
        }},
        "reason": "A brief statement on why they are a good starting point for the user.",
        "next_steps": "Specific, actionable next steps the user should take."
      }}
    ]
    ```
    """

    response = await openrouter_llm.ainvoke([
        SystemMessage(content="You are an expert immigration consultant providing personalized lawyer recommendations."),
        HumanMessage(content=recommendation_prompt)
    ])

    # Parse recommendations
    recommendations_text = response.content
    json_match = re.search(r'\[.*\]', recommendations_text, re.DOTALL)

    if json_match:
        recommendations = json.loads(json_match.group())
    else:
        # Create default recommendations
        sorted_lawyers = state["lawyer_profiles"][:2]

        recommendations = []
        for i, lawyer in enumerate(sorted_lawyers):
            recommendations.append({
                "rank": i + 1,
                "lawyer": lawyer.model_dump(),
                "why_recommended": [
                    f"Found profile for {lawyer.name} specializing in EB-1A cases.",
                    "Contact information is available to start the process."
                ],
                "next_steps": [
                    f"Schedule initial consultation via {lawyer.contact_info.get('email', 'their website')}",
                    "Prepare your CV and list of achievements for discussion",
                    "Inquire about their specific experience with cases like yours.",
                ]
            })

    state["recommendations"] = recommendations

    # Generate final reasoning
    reasoning_prompt = f"""
    Summarize why these lawyers were selected for the user in 2-3 sentences.
    User priorities: {user_profile.priority_factors}
    Selected lawyers: {[r['lawyer']['name'] for r in recommendations]}
    """

    reasoning_response = await openrouter_llm.ainvoke([HumanMessage(content=reasoning_prompt)])
    state["reasoning"] = reasoning_response.content

    state["messages"].append(f"Generated {len(recommendations)} lawyer recommendations")
    return state