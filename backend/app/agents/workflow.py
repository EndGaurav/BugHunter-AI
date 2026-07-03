from langgraph.graph import StateGraph, END
from app.agents.state import AgentState, PRReviewResult
from app.agents.memory_logic import retrieve_context
from app.core.config import settings
from openai import OpenAI
import logging
import json

logger = logging.getLogger(__name__)

# Initialize client for AWS Bedrock OpenAI-compatible API
# You may need to change the base_url depending on your region or setup
client = OpenAI(
    api_key=settings.AWS_BEARER_TOKEN_BEDROCK,
    base_url="https://bedrock-runtime.us-east-1.amazonaws.com/v1" # update region if needed
) if settings.AWS_BEARER_TOKEN_BEDROCK else None

async def retrieve_context_node(state: AgentState) -> dict:
    """Node that fetches memory context for the PR diff."""
    logger.info(f"Running retrieve_context_node for PR #{state.get('pr_number')}")
    context = await retrieve_context(state.get("parsed_files", {}))
    return {"memory_context": context}

async def analyze_pr_node(state: AgentState) -> dict:
    """Node that uses Groq to analyze the PR against the memory context."""
    logger.info(f"Running analyze_pr_node for PR #{state.get('pr_number')}")
    if not client:
        logger.warning("AWS Bedrock API key not configured, skipping analysis.")
        return {"analysis_result": PRReviewResult(risk_level="Unknown", potential_bugs=[], general_feedback="API key not configured.")}
        
    diff_text = ""
    for fname, diff in state.get("parsed_files", {}).items():
        diff_text += f"\nFile: {fname}\n{diff}\n"
        
    prompt = f"""
    You are an expert code reviewer.
    Review the following PR diff, keeping in mind this historical context from our memory layer:
    {state.get('memory_context', 'No context available.')}
    
    Diff:
    {diff_text}
    
    You must output ONLY valid JSON that matches this schema:
    {{
      "risk_level": "Low, Medium, High, or Critical",
      "potential_bugs": ["list of strings"],
      "general_feedback": "string"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="meta.llama3-1-8b-instruct-v1:0",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        # Parse the structured JSON response into our Pydantic model
        result_json = response.choices[0].message.content
        result = PRReviewResult.model_validate_json(result_json)
        return {"analysis_result": result}
    except Exception as e:
        logger.error(f"Error during LLM analysis: {e}")
        return {"analysis_result": PRReviewResult(risk_level="Error", potential_bugs=[], general_feedback=str(e))}

def build_workflow():
    """Builds and compiles the LangGraph state graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("analyze_pr", analyze_pr_node)
    
    # Define edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "analyze_pr")
    workflow.add_edge("analyze_pr", END)
    
    return workflow.compile()
    
# Export the compiled graph
pr_reviewer_graph = build_workflow()
