from langgraph.graph import StateGraph, END
from app.agents.state import AgentState, PRReviewResult
from app.agents.memory_logic import retrieve_context
from app.core.config import settings
import os
# Ensure AWS region is set before litellm import for Bedrock URL construction
os.environ["AWS_REGION_NAME"] = "us-east-1"
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
import litellm
import logging
import json

logger = logging.getLogger(__name__)

import os
import os
import random
import asyncio
# Drop unsupported params for litellm Bedrock requests
litellm.drop_params = True
os.environ["AWS_REGION_NAME"] = "us-east-1"

async def retrieve_context_node(state: AgentState) -> dict:
    """Node that fetches memory context for the PR diff."""
    logger.info(f"Running retrieve_context_node for PR #{state.get('pr_number')}")
    context = await retrieve_context(state.get("parsed_files", {}))
    return {"memory_context": context}

async def analyze_pr_node(state: AgentState) -> dict:
    """Node that uses LLM to analyze the PR against the memory context."""
    logger.info(f"Running analyze_pr_node for PR #{state.get('pr_number')}")
    if not settings.AWS_BEARER_TOKEN_BEDROCK:
        logger.warning("AWS Bedrock API key not configured, skipping analysis.")
        return {"analysis_result": PRReviewResult(risk_level="Unknown", potential_bugs=[], general_feedback="API key not configured.")}
        
    diff_text = ""
    for fname, diff in state.get("parsed_files", {}).items():
        diff_text += f"\nFile: {fname}\n{diff}\n"
        
    # Truncate to prevent Bedrock RateLimitError / Too many tokens
    # Llama 3 8B on Bedrock typically has an 8k context window.
    # Reduce diff size further to avoid Bedrock token limits and rate limiting
    max_chars = 4000
    if len(diff_text) > max_chars:
        logger.warning(f"Diff too large ({len(diff_text)} chars), truncating to {max_chars} chars.")
        diff_text = diff_text[:max_chars] + "\n... [TRUNCATED DUE TO LENGTH]"
        
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
    
    # Small initial delay to avoid burst rate limits
    await asyncio.sleep(1)
    # Attempt LLM call with simple retry on RateLimitError
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = litellm.completion(
                model="bedrock/meta.llama3-8b-instruct-v1:0",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.0,
            )
            result_json = response.choices[0].message.content
            result = PRReviewResult.model_validate_json(result_json)
            return {"analysis_result": result}
        except litellm.exceptions.RateLimitError as rl_err:
            logger.warning(f"Rate limit hit on attempt {attempt}: {rl_err}. Retrying after backoff...")
            backoff = 2 ** attempt
            jitter = random.random()
            await asyncio.sleep(backoff + jitter)
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}")
            return {"analysis_result": PRReviewResult(risk_level="Error", potential_bugs=[], general_feedback=str(e))}
    # If all retries exhausted
    logger.error("LLM analysis failed after retries due to rate limiting.")
    return {"analysis_result": PRReviewResult(risk_level="Error", potential_bugs=[], general_feedback="Rate limit exceeded.")}

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
