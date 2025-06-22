from models import AgentState, LawyerProfile, UserProfile
from prompts import LAWYER_FINDER_AGENT_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import os
import re
from dotenv import load_dotenv
import asyncio

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
    1. EB-1A lawyers with high success rates (90%+) and their experience level
    2. Lawyers experienced with {user_profile.nationality} nationals and their years practicing
    3. Lawyers specializing in {user_profile.industry} with their firm websites
    4. Location-specific lawyers if applicable with their professional background
    5. Lawyers within the budget range and their experience

    Format your response as a JSON array of search queries.
    Focus on finding lawyers with verifiable success rates, years of experience, and official websites.
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
            f"EB-1A immigration lawyers 90% success rate {user_profile.industry} years experience website",
            f"Top EB-1A attorneys {user_profile.nationality} extraordinary ability visa firm website experience",
            f"Best EB-1A lawyers high approval rate {user_profile.location_preference or 'USA'} professional background",
            f"Immigration lawyers EB-1A {user_profile.occupation} cases statistics years practicing",
            "EB-1A visa attorneys success rate data verified results official websites experience"
        ]

    state["search_queries"] = queries
    state["messages"].append(f"Generated {len(queries)} search queries")
    return state

# Node 2: Execute Perplexity Search
async def search_with_perplexity(state: AgentState) -> AgentState:
    """Execute searches using Perplexity API in parallel."""

    async def search_single_query(query: str) -> dict:
        """Execute a single search query."""
        perplexity_prompt = f"""
        Search for information about EB-1A immigration lawyers with the following query:
        "{query}"

        Focus on finding:
        - Lawyer names and their law firms
        - Years of experience practicing immigration law
        - Official website URLs of the lawyer, not the firm's website
        - Professional background and qualifications
        - Client testimonials mentioning experience level

        Provide detailed, factual information with sources when available.
        """

        try:
            response = await perplexity_llm.ainvoke([
                SystemMessage(content="You are a helpful assistant finding information about immigration lawyers."),
                HumanMessage(content=perplexity_prompt)
            ])

            return {
                "query": query,
                "results": response.content
            }

        except Exception as e:
            state["messages"].append(f"Error searching with Perplexity for query '{query}': {str(e)}")
            # Fallback to mock data
            return {
                "query": query,
                "results": f"Mock search results for: {query}"
            }

    # Create tasks for all queries
    search_tasks = [search_single_query(query) for query in state["search_queries"]]
    
    # Execute all searches in parallel
    all_results = await asyncio.gather(*search_tasks)

    state["raw_search_results"] = all_results
    state["messages"].append(f"Completed {len(all_results)} searches in parallel")
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
    - Law firm name
    - Official website URL of the lawyer, not the firm's website(must be a valid URL)
    - Years of experience (estimate if exact number not found based on career timeline)

    IMPORTANT RULES:
    1. Verify the lawyer specializes in EB-1A specifically, not just general immigration.
    2. Only include lawyers where you can find or reasonably estimate their experience level.
    3. Website must be a valid URL (starting with http:// or https://) and must be the lawyer's website, not the firm's website
    4. If years of experience is not explicitly stated, estimate based on:
       - When they started practicing law
       - When they joined their current firm
       - Career milestones mentioned
    5. Be conservative with experience estimates (round down rather than up)

    Return the profiles as a JSON array. Each profile should match this structure:
    {{
        "name": "string",
        "firm": "string", 
        "website": "string (valid URL)",
        "years_experience": number (integer)
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
            lawyer_profiles = []
            
            for profile in profiles_data:
                # Validate the profile has required fields
                if all(key in profile for key in ['name', 'firm', 'website', 'years_experience']):
                    # Ensure website has proper format
                    if not profile['website'].startswith(('http://', 'https://')):
                        profile['website'] = 'https://' + profile['website']
                    
                    lawyer_profiles.append(LawyerProfile(**profile))
                    
        except (json.JSONDecodeError, TypeError, ValueError) as e:
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

    Based on the available information, recommend the TOP 3 lawyers for this user.
    Consider their years of experience and how it aligns with the user's needs.

    Your response MUST be a single, valid JSON array. Each object in the array represents one
    lawyer recommendation and MUST conform to the exact structure below. Do not add any
    introductory text or explanations outside of the JSON structure.

    If a lawyer profile does not have a website, do not include them in the recommendations.

    ```json
    [
      {{
        "lawyer": {{
          "name": "Lawyer's Full Name",
          "firm": "Name of the Law Firm",
          "website": "https://www.lawfirm.com",
          "years_experience": 15
        }},
        "reason": "A brief statement on why they are a good match, considering their experience level and expertise.",
        "rating": "A rating out of 100 for the lawyer's expertise and experience. It should be based on the ranks (top 1 lawyer should have higher ratting than the 2nd and 3rd, similarly for the 2nd and 3rd)"
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
        print("No recommendations found, creating default recommendations")
        sorted_lawyers = sorted(state["lawyer_profiles"], key=lambda x: x.years_experience, reverse=True)

        recommendations = []
        for i, lawyer in enumerate(sorted_lawyers):
            recommendations.append({
                "rank": i + 1,
                "lawyer": lawyer.model_dump(),
                "why_recommended": [
                    f"{lawyer.name} from {lawyer.firm} has {lawyer.years_experience} years of experience in immigration law.",
                    f"Specializes in EB-1A cases with extensive experience in the field.",
                    f"Visit their website at {lawyer.website} for more information."
                ],
                "rating": 100 - ((i+1) * 5)
            })

    state["recommendations"] = recommendations

    # Generate final reasoning
    reasoning_prompt = f"""
    Summarize why these lawyers were selected for the user in 2-3 sentences.
    User priorities: {user_profile.priority_factors}
    Selected lawyers: {[r['lawyer']['name'] + ' (' + str(r['lawyer']['years_experience']) + ' years experience)' for r in recommendations]}
    """

    reasoning_response = await openrouter_llm.ainvoke([HumanMessage(content=reasoning_prompt)])
    state["reasoning"] = reasoning_response.content

    state["messages"].append(f"Generated {len(recommendations)} lawyer recommendations")
    return state