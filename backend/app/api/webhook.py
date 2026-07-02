from fastapi import APIRouter, Request, HTTPException
from app.services.github import extract_pr_diff, parse_modified_code
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def github_webhook(request: Request):
    """
    Webhook receiver for GitHub PR events.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    event_type = request.headers.get("x-github-event", "")
    
    # Respond to GitHub's ping event
    if event_type == "ping":
        return {"status": "success", "message": "Pong!"}
        
    # We only care about Pull Requests for now
    if event_type != "pull_request":
        return {"status": "ignored", "message": f"Ignoring event type: {event_type}"}
        
    action = payload.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return {"status": "ignored", "message": f"Ignoring PR action: {action}"}
        
    pr_data = payload.get("pull_request", {})
    diff_url = pr_data.get("diff_url")
    pr_number = pr_data.get("number")
    repo_name = payload.get("repository", {}).get("full_name")
    
    if not diff_url:
        raise HTTPException(status_code=400, detail="No diff_url found in payload")
        
    try:
        # 1. Fetch raw diff from GitHub
        raw_diff = await extract_pr_diff(diff_url)
        
        # 2. Parse the modified code
        parsed_files = parse_modified_code(raw_diff)
        
        from app.agents.workflow import pr_reviewer_graph
        from app.agents.state import AgentState
        
        # 3. Trigger LangGraph Workflow
        initial_state: AgentState = {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "parsed_files": parsed_files,
            "memory_context": None,
            "analysis_result": None
        }
        
        logger.info(f"Triggering workflow for PR #{pr_number}")
        final_state = await pr_reviewer_graph.ainvoke(initial_state)
        
        analysis = final_state.get("analysis_result")
        analysis_dict = analysis.model_dump() if analysis and hasattr(analysis, 'model_dump') else analysis
        
        # Print the analysis to the terminal so we can see it during the demo!
        print("\n" + "="*50)
        print(f"[AI] Groq Analysis for PR #{pr_number}")
        print("="*50)
        import json
        print(json.dumps(analysis_dict, indent=2))
        print("="*50 + "\n")
        
        return {
            "status": "success",
            "message": f"Successfully processed PR #{pr_number}",
            "files_changed": list(parsed_files.keys()),
            "analysis": analysis_dict
        }
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while processing diff")
