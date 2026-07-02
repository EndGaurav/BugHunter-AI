from typing import TypedDict, Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PRReviewResult(BaseModel):
    risk_level: str = Field(description="The risk level of the PR: Low, Medium, High, or Critical")
    potential_bugs: List[str] = Field(description="A list of potential bugs or issues identified in the code")
    general_feedback: str = Field(description="General feedback or suggestions for improvement")

class AgentState(TypedDict):
    pr_number: int
    repo_name: str
    parsed_files: Dict[str, str]  # filename -> diff content
    memory_context: Optional[str] # Mocked context from Cognee
    analysis_result: Optional[PRReviewResult] # The structured output from Gemini
