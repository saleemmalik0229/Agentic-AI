from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class ResearchStep(BaseModel):
    step_id: int
    description: str
    tool: str  # e.g., "search", "arxiv", "analysis"
    query: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None

class ResearchPlan(BaseModel):
    goal: str
    steps: List[ResearchStep]

class AgentState(BaseModel):
    """The state of the LangGraph execution."""
    user_query: str
    plan: Optional[ResearchPlan] = None
    steps: List[ResearchStep] = []
    current_step_index: int = 0
    artifacts: Dict[str, Any] = {}
    final_answer: Optional[str] = None
    messages: List[str] = []

class UserQueryRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    query: str
    answer: str
    trace: List[ResearchStep]
