from typing import TypedDict, List, Optional, Dict, Annotated
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Pydantic Models
class LawyerProfile(BaseModel):
    name: str
    firm: str
    website: str
    years_experience: int
    # location: str
    # eb1a_cases_handled: int
    # success_rate: float
    # specializations: List[str]
    # average_processing_time: str
    # fee_range: Dict[str, float]
    # client_industries: List[str]
    # notable_achievements: List[str]

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
    raw_search_results: List[Dict]
    lawyer_profiles: List[LawyerProfile]
    compatibility_scores: Dict[str, float]
    recommendations: List[Dict]
    reasoning: str
    messages: Annotated[List[BaseMessage], add_messages]  # LangChain messages with reducer