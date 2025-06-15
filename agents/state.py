# agents/state.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentState(BaseModel):
    """Pydantic model for our LangGraph state."""
    user_name: str = Field(default="", description="The name of the user for personalization.")
    skill_level: str = Field(default="Intermediate", description="User's selected skill level.")
    
    problem_id: int = Field(..., description="The ID of the current DSA problem.")
    problem_details: Dict[str, Any] = Field(..., description="Full details of the current problem.")
    
    user_input: str = Field(default="", description="The latest input from the user.")
    code: str = Field(default="", description="The current code submitted by the user.")
    
    messages: List[Dict[str, str]] = Field(default_factory=list, description="The history of the chat conversation.")
    persona: Dict[str, str] = Field(default_factory=dict, description="The AI's current persona settings.")
    
    hints_used: int = Field(default=0, description="Counter for hints requested by the user.")
    
    # Store test and code review results
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Results from TestingAgent.")
    code_review: Dict[str, Any] = Field(default_factory=dict, description="Results from CodeAgent.")
    
    # Controls the flow of the graph
    current_step: str = Field(..., description="The next step for the orchestrator to route to.")
    
    # For long-term tracking
    session_id: str
    historical_session_summaries: List[str] = Field(default_factory=list, description="Summaries from past sessions.")