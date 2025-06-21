from models import AgentState, LawyerProfile, UserProfile
from prompts import LAWYER_FINDER_AGENT_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
from langchain_openai import ChatOpenAI
import json
import os
import re
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# LLM for Perplexity Search
perplexity_llm = ChatOpenAI(
    model="sonar",
    api_key=os.environ.get("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

# LLM for other tasks (generation, extraction, scoring)
openrouter_llm = ChatOpenAI(
    model="mistralai/mistral-small-3.2-24b-instruct:free",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


async def generate_search_queries(state: AgentState) -> Dict[str, Any]:
    """Generate targeted search queries based on user profile."""
    
    user_profile = state["user_profile"]
    
    # Add message about starting search query generation
    messages = [
        AIMessage(content=f"Generating search queries for {user_profile.occupation} in {user_profile.industry}...")
    ]
    
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
    
    # Add success message
    messages.append(
        AIMessage(content=f"Generated {len(queries)} targeted search queries based on user profile")
    )
    
    return {
        "search_queries": queries,
        "messages": messages
    }


async def search_with_perplexity(state: AgentState) -> Dict[str, Any]:
    """Execute searches using Perplexity API."""
    
    messages = []
    all_results = []
    
    # Add search start message
    messages.append(
        SystemMessage(content=f"Starting Perplexity search with {len(state['search_queries'])} queries")
    )
    
    for i, query in enumerate(state["search_queries"]):
        perplexity_prompt = f"""
        Search for information about EB-1A immigration lawyers with the following query:
        "{query}"
        
        Focus on finding:
        - Lawyer names and firms
        - Success rates and approval percentages
        - Number of EB-1A cases handled
        - Client testimonials
        - Fee structures
        - Industry specializations
        - Contact information
        
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
            
            # Add search progress message
            messages.append(
                ToolMessage(
                    content=f"Search {i+1}/{len(state['search_queries'])} completed: Found results for '{query[:50]}...'",
                    tool_call_id=f"search_{i+1}"
                )
            )
            
        except Exception as e:
            error_msg = f"Error searching with Perplexity for query '{query[:50]}...': {str(e)}"
            messages.append(SystemMessage(content=error_msg))
            
            # Fallback to regular LLM with mock data
            all_results.append({
                "query": query,
                "results": f"Mock search results for: {query}"
            })
    
    # Add completion message
    messages.append(
        AIMessage(content=f"Completed all searches. Found {len(all_results)} sets of results to analyze.")
    )
    
    return {
        "raw_search_results": all_results,
        "messages": messages
    }


async def extract_lawyer_profiles(state: AgentState) -> Dict[str, Any]:
    """Extract structured lawyer profiles from search results."""
    
    messages = []
    
    # Add extraction start message
    messages.append(
        AIMessage(content="Analyzing search results to extract qualified lawyer profiles...")
    )
    
    extraction_prompt = f"""
    You are an expert at extracting structured information about lawyers from search results.
    
    Search Results:
    {json.dumps(state["raw_search_results"], indent=2)}
    
    Extract information about EB-1A immigration lawyers and create detailed profiles.
    
    For each lawyer found, extract:
    - Full name and law firm
    - Location (city, state)
    - Years of experience in immigration law
    - Number of EB-1A cases handled (estimate if not exact)
    - Success rate (percentage, must be 85% or higher to include)
    - Industry specializations
    - Average processing time for EB-1A cases
    - Fee range (min and max in USD)
    - Types of clients they typically work with
    - Notable achievements or recognitions
    - Contact information (email, phone, website)
    
    IMPORTANT RULES:
    1. Only include lawyers with explicitly stated or clearly implied success rates of 85% or higher
    2. If success rate is not mentioned, do not include that lawyer
    3. Verify the lawyer specializes in EB-1A specifically, not just general immigration
    4. Provide realistic estimates based on industry standards when exact data is not available
    
    Return the profiles as a JSON array. Each profile should match this structure:
    {{
        "name": "string",
        "firm": "string",
        "location": "string",
        "years_experience": number,
        "eb1a_cases_handled": number,
        "success_rate": number (as percentage, e.g., 92.5),
        "specializations": ["string"],
        "average_processing_time": "string",
        "fee_range": {{"min": number, "max": number}},
        "client_industries": ["string"],
        "notable_achievements": ["string"],
        "contact_info": {{"email": "string", "phone": "string", "website": "string"}}
    }}
    """
    
    try:
        response = await openrouter_llm.ainvoke([
            SystemMessage(content="You are an expert at extracting and structuring lawyer information from text."),
            HumanMessage(content=extraction_prompt)
        ])
        
        # Parse lawyer profiles
        profiles_text = response.content
        json_match = re.search(r'\[.*\]', profiles_text, re.DOTALL)
        
        if json_match:
            profiles_data = json.loads(json_match.group())
            lawyer_profiles = [LawyerProfile(**profile) for profile in profiles_data]
            
            # Add success message with details
            profile_summary = "\n".join([
                f"- {p.name} ({p.firm}): {p.success_rate}% success rate, {p.eb1a_cases_handled} EB-1A cases"
                for p in lawyer_profiles[:3]
            ])
            
            messages.append(
                AIMessage(
                    content=f"Successfully extracted {len(lawyer_profiles)} qualified lawyer profiles:\n{profile_summary}"
                )
            )
        else:
            # No profiles found
            messages.append(
                SystemMessage(content="Could not find any lawyer profiles matching the criteria in search results.")
            )
            lawyer_profiles = []
            
    except (json.JSONDecodeError, TypeError) as e:
        error_msg = f"Error parsing lawyer profiles: {str(e)}. No profiles extracted."
        messages.append(SystemMessage(content=error_msg))
        lawyer_profiles = []
    
    return {
        "lawyer_profiles": lawyer_profiles,
        "messages": messages
    }


async def calculate_compatibility(state: AgentState) -> Dict[str, Any]:
    """Calculate compatibility scores between user and lawyers."""
    
    messages = []
    user_profile = state["user_profile"]
    
    # Add analysis start message
    messages.append(
        AIMessage(
            content=f"Calculating compatibility scores for {len(state['lawyer_profiles'])} lawyers based on user priorities: {', '.join(user_profile.priority_factors)}"
        )
    )
    
    compatibility_prompt = f"""
    You are an expert at matching clients with lawyers based on compatibility factors.
    
    User Profile:
    {user_profile.model_dump_json(indent=2)}
    
    Lawyer Profiles:
    {json.dumps([lawyer.model_dump() for lawyer in state["lawyer_profiles"]], indent=2)}
    
    Calculate a compatibility score (0-100) for each lawyer based on:
    
    1. Success Rate (40% weight):
       - 95%+ = 40 points
       - 90-94% = 35 points
       - 85-89% = 30 points
    
    2. Industry Match (20% weight):
       - Perfect match = 20 points
       - Related industry = 15 points
       - Some experience = 10 points
       - No specific experience = 5 points
    
    3. Budget Alignment (15% weight):
       - Within budget = 15 points
       - Slightly above (up to 20%) = 10 points
       - Significantly above = 5 points
    
    4. Location Match (10% weight):
       - Same city = 10 points
       - Same state = 7 points
       - Different location = 5 points
    
    5. Experience with Nationality (10% weight):
       - Extensive experience = 10 points
       - Some experience = 7 points
       - No specific experience = 3 points
    
    6. Timeline Fit (5% weight):
       - Matches urgency = 5 points
       - Acceptable = 3 points
       - Too slow = 1 point
    
    Return a JSON object with lawyer names as keys and scores as values.
    Also provide a brief reasoning for each score.
    
    Format:
    {{
        "lawyer_name": {{
            "score": number,
            "breakdown": {{
                "success_rate": number,
                "industry_match": number,
                "budget_alignment": number,
                "location_match": number,
                "nationality_experience": number,
                "timeline_fit": number
            }},
            "reasoning": "string"
        }}
    }}
    """
    
    try:
        response = await openrouter_llm.ainvoke([
            SystemMessage(content="You are an expert at calculating compatibility scores between clients and lawyers."),
            HumanMessage(content=compatibility_prompt)
        ])
        
        # Parse compatibility scores
        scores_text = response.content
        json_match = re.search(r'\{.*\}', scores_text, re.DOTALL)
        
        if json_match:
            scores_data = json.loads(json_match.group())
            compatibility_scores = {}
            
            # Extract scores and add messages for high compatibility matches
            for lawyer_name, score_info in scores_data.items():
                score = score_info["score"]
                compatibility_scores[lawyer_name] = score
                
                # Add detailed message for high compatibility lawyers
                if score >= 85:
                    messages.append(
                        AIMessage(
                            content=f"High compatibility match: {lawyer_name} (Score: {score}/100) - {score_info.get('reasoning', 'Strong match across multiple factors')}"
                        )
                    )
        else:
            # Fallback scoring
            compatibility_scores = {}
            for lawyer in state["lawyer_profiles"]:
                base_score = lawyer.success_rate * 0.4
                industry_bonus = 15 if user_profile.industry in lawyer.specializations else 10
                budget_bonus = 15 if lawyer.fee_range["min"] <= user_profile.budget_range["max"] else 5
                compatibility_scores[lawyer.name] = min(base_score + industry_bonus + budget_bonus, 100)
            
            messages.append(
                SystemMessage(content="Used fallback compatibility scoring based on key factors.")
            )
            
    except Exception as e:
        messages.append(
            SystemMessage(content=f"Error calculating compatibility scores: {str(e)}. Using default scoring.")
        )
        # Use empty scores
        compatibility_scores = {}
    
    # Add summary message
    if compatibility_scores:
        top_scores = sorted(compatibility_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        summary = "Top compatibility matches: " + ", ".join([f"{name} ({score:.0f})" for name, score in top_scores])
        messages.append(AIMessage(content=summary))
    
    return {
        "compatibility_scores": compatibility_scores,
        "messages": messages
    }


async def generate_recommendations(state: AgentState) -> Dict[str, Any]:
    """Generate final lawyer recommendations."""
    
    messages = []
    user_profile = state["user_profile"]
    
    # Check if we have lawyer profiles
    if not state.get("lawyer_profiles"):
        messages.extend([
            SystemMessage(content="No lawyer profiles available for recommendations."),
            AIMessage(content="Unable to generate recommendations due to lack of qualified lawyer profiles in search results.")
        ])
        
        return {
            "recommendations": [],
            "reasoning": "No qualified lawyers found in the search results.",
            "messages": messages
        }
    
    # Add recommendation generation start message
    messages.append(
        AIMessage(content="Generating personalized recommendations based on compatibility analysis...")
    )
    
    recommendation_prompt = f"""
    You are an expert at making personalized lawyer recommendations for EB-1A visa applications.
    
    User Profile:
    {user_profile.model_dump_json(indent=2)}
    
    Lawyer Profiles:
    {json.dumps([lawyer.model_dump() for lawyer in state["lawyer_profiles"]], indent=2)}
    
    Compatibility Scores:
    {json.dumps(state.get("compatibility_scores", {}), indent=2)}
    
    Based on the analysis, recommend the TOP 2 lawyers for this user.
    
    Return ONLY a valid JSON array. Each item should have this structure:
    {{
        "rank": 1,
        "lawyer_name": "Full Name",
        "lawyer_firm": "Firm Name",
        "success_rate": 95.0,
        "compatibility_score": 85,
        "why_recommended": ["reason1", "reason2", "reason3"],
        "estimated_timeline": "8-12 months",
        "estimated_total_cost": "$20,000 - $30,000"
    }}
    
    Return ONLY the JSON array, no other text.
    """
    
    try:
        response = await openrouter_llm.ainvoke([
            SystemMessage(content="You are an expert immigration consultant. Return only valid JSON."),
            HumanMessage(content=recommendation_prompt)
        ])
        
        # Parse recommendations
        recommendations_text = response.content.strip()
        
        # Try to parse JSON
        try:
            parsed_recommendations = json.loads(recommendations_text)
        except json.JSONDecodeError:
            # Try to extract JSON array from text
            json_match = re.search(r'\[.*\]', recommendations_text, re.DOTALL)
            if json_match:
                parsed_recommendations = json.loads(json_match.group())
            else:
                parsed_recommendations = None
        
        # Convert to expected format
        recommendations = []
        if parsed_recommendations and isinstance(parsed_recommendations, list):
            for i, rec in enumerate(parsed_recommendations):
                # Find matching lawyer profile
                lawyer_profile = None
                lawyer_name = rec.get("lawyer_name", "")
                
                for lawyer in state["lawyer_profiles"]:
                    if lawyer.name == lawyer_name or lawyer.name in str(rec):
                        lawyer_profile = lawyer
                        break
                
                # If no exact match, use the i-th lawyer if available
                if not lawyer_profile and i < len(state["lawyer_profiles"]):
                    lawyer_profile = state["lawyer_profiles"][i]
                
                if lawyer_profile:
                    formatted_rec = {
                        "rank": rec.get("rank", i + 1),
                        "lawyer": {
                            "name": lawyer_profile.name,
                            "firm": lawyer_profile.firm,
                            "success_rate": lawyer_profile.success_rate,
                            "location": lawyer_profile.location
                        },
                        "compatibility_score": rec.get("compatibility_score", 
                                                      state.get("compatibility_scores", {}).get(lawyer_profile.name, 80)),
                        "why_recommended": rec.get("why_recommended", [
                            f"Success rate: {lawyer_profile.success_rate}%",
                            f"Specializes in {', '.join(lawyer_profile.specializations[:2])}",
                            f"Experience: {lawyer_profile.eb1a_cases_handled} EB-1A cases"
                        ]),
                        "estimated_timeline": rec.get("estimated_timeline", lawyer_profile.average_processing_time),
                        "estimated_total_cost": rec.get("estimated_total_cost", 
                                                       f"${lawyer_profile.fee_range['min']:,} - ${lawyer_profile.fee_range['max']:,}"),
                        "next_steps": [
                            f"Contact: {lawyer_profile.contact_info.get('email', 'See website')}",
                            "Schedule initial consultation",
                            "Prepare your documentation"
                        ]
                    }
                    recommendations.append(formatted_rec)
                    
                    # Add recommendation message
                    messages.append(
                        AIMessage(
                            content=f"Recommendation #{rec.get('rank', i + 1)}: {lawyer_profile.name} from {lawyer_profile.firm} - "
                                   f"{rec.get('compatibility_score', 80)}% compatibility, "
                                   f"{lawyer_profile.success_rate}% success rate"
                        )
                    )
        
    except Exception as e:
        error_msg = f"Error generating recommendations: {str(e)}"
        messages.append(SystemMessage(content=error_msg))
        recommendations = None
    
    # Fallback if LLM fails or no recommendations
    if not recommendations:
        messages.append(
            SystemMessage(content="Using fallback recommendation method based on scores and success rates.")
        )
        
        sorted_lawyers = sorted(
            state["lawyer_profiles"], 
            key=lambda l: (l.success_rate, state.get("compatibility_scores", {}).get(l.name, 0)), 
            reverse=True
        )[:2]
        
        recommendations = []
        for i, lawyer in enumerate(sorted_lawyers):
            rec = {
                "rank": i + 1,
                "lawyer": {
                    "name": lawyer.name,
                    "firm": lawyer.firm,
                    "success_rate": lawyer.success_rate,
                    "location": lawyer.location
                },
                "compatibility_score": state.get("compatibility_scores", {}).get(lawyer.name, 0),
                "why_recommended": [
                    f"Outstanding {lawyer.success_rate}% success rate with EB-1A cases",
                    f"Specializes in {', '.join(lawyer.specializations[:2]) if lawyer.specializations else 'immigration law'}",
                    f"Handled {lawyer.eb1a_cases_handled} EB-1A cases successfully"
                ],
                "estimated_timeline": lawyer.average_processing_time,
                "estimated_total_cost": f"${lawyer.fee_range['min']:,} - ${lawyer.fee_range['max']:,}",
                "next_steps": [
                    f"Email: {lawyer.contact_info.get('email', 'Not available')}",
                    f"Phone: {lawyer.contact_info.get('phone', 'Not available')}",
                    "Schedule consultation to discuss your case"
                ]
            }
            recommendations.append(rec)
            
            messages.append(
                AIMessage(
                    content=f"Recommendation #{i + 1}: {lawyer.name} - Selected for high success rate and experience"
                )
            )
    
    # Generate reasoning
    reasoning = "Top lawyers selected based on EB-1A success rates and compatibility."
    
    try:
        lawyer_names = []
        for r in recommendations:
            if isinstance(r, dict) and 'lawyer' in r and isinstance(r['lawyer'], dict):
                lawyer_names.append(r['lawyer'].get('name', 'Unknown'))
        
        if lawyer_names:
            reasoning_prompt = f"""
            Summarize why these lawyers were selected for the user in 2-3 sentences.
            User priorities: {user_profile.priority_factors}
            Selected lawyers: {lawyer_names}
            """
            
            try:
                reasoning_response = await openrouter_llm.ainvoke([HumanMessage(content=reasoning_prompt)])
                reasoning = reasoning_response.content
                
                # Add final reasoning message
                messages.append(
                    AIMessage(content=f"Selection rationale: {reasoning}")
                )
            except:
                reasoning = f"Selected {', '.join(lawyer_names)} based on their high success rates and experience with {user_profile.industry} professionals."
    except Exception as e:
        pass
    
    # Add completion message
    messages.append(
        SystemMessage(content=f"Recommendation process complete. Generated {len(recommendations)} recommendations.")
    )
    
    return {
        "recommendations": recommendations,
        "reasoning": reasoning,
        "messages": messages
    }