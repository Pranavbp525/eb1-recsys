from typing import TypedDict, List, Optional, Dict, Annotated
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Pydantic Models
class LawyerProfile(BaseModel):
    name: str
    firm: str
    # location: str
    # years_experience: int
    # eb1a_cases_handled: int
    # success_rate: float
    # specializations: List[str]
    # average_processing_time: str
    # fee_range: Dict[str, float]
    # client_industries: List[str]
    # notable_achievements: List[str]
    contact_info: Dict[str, str]

class UserProfile(BaseModel):
    name: str
    occupation: str
    industry: str
    nationality: str
    budget_range: Dict[str, float]
    location_preference: Optional[str] = None
    timeline_urgency: str  # "urgent", "moderate", "flexible"
    achievements: List[str]
    publications: Optional[int] = None
    citations: Optional[int] = None
    awards: Optional[List[str]] = None
    priority_factors: List[str]  # e.g., ["success_rate", "cost", "location"]

# State Definition
class AgentState(TypedDict):
    user_profile: UserProfile
    search_queries: List[str]
    raw_search_results: List[dict]
    lawyer_profiles: List[LawyerProfile]
    recommendations: List[dict]
    reasoning: str
    messages: List[str]