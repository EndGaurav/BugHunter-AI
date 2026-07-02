"""
Run this script once to seed Cognee's memory with historical bug data.
Usage: uv run python -m app.scripts.seed_bugs
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# CRITICAL: Set all environment variables BEFORE importing cognee,
# because Cognee reads its config at module import time.
groq_api_key = os.getenv("GROQ_API_KEY", "")

# Cognee uses LiteLLM internally. LiteLLM supports Groq natively via the
# "groq/" model prefix. We use 'openai' as the Cognee provider since
# 'groq' is not in Cognee's LLMProvider enum, but pass "groq/model" as
# the model name so LiteLLM routes it correctly.
os.environ["LLM_API_KEY"] = groq_api_key
os.environ["LLM_MODEL"] = "groq/llama-3.1-8b-instant"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["EMBEDDING_PROVIDER"] = "fastembed"

# Skip Cognee's pre-flight LLM connection test (it doesn't support custom
# provider routing in its test runner, but the actual calls will work fine).
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

import cognee

HISTORICAL_BUGS = [
    """Bug #101: NullPointerException in webhook parser.
    File: app/api/webhook.py
    Description: When a PR is opened with no files changed, the diff_url returns an empty string. 
    The parser crashed because it tried to iterate over an empty dict without a null check.
    Resolution: Added a guard clause to check if diff_url is empty before proceeding.""",

    """Bug #102: Race condition in async LLM call.
    File: app/agents/workflow.py
    Description: When multiple PRs were submitted simultaneously, the shared Groq client instance 
    was overwritten mid-request, causing wrong responses to be returned for concurrent requests.
    Resolution: Changed the client to be instantiated per-request instead of a global singleton.""",

    """Bug #103: Incorrect diff parsing for renamed files.
    File: app/services/github.py
    Description: The parse_modified_code function did not handle the 'rename from / rename to' 
    git diff format. Renamed files were being silently dropped from the analysis.
    Resolution: Added handling for the 'rename' diff block format.""",

    """Bug #104: Cognee query timeout on large repositories.
    File: app/agents/memory_logic.py
    Description: Querying Cognee for repositories with hundreds of past bugs caused a timeout 
    because there was no top_k limit set on the recall query.
    Resolution: Added top_k=5 to the recall query to limit results.""",

    """Bug #105: Missing authentication on webhook endpoint.
    File: app/api/webhook.py
    Description: The /webhook endpoint was publicly accessible without verifying the 
    GitHub webhook secret signature (x-hub-signature-256 header). This allowed anyone 
    to spoof GitHub events.
    Resolution: Added HMAC-SHA256 signature verification against the GitHub webhook secret.""",
]

async def seed():
    print("[*] Starting Cognee seeding process...")
    await cognee.prune.prune_data()
    print("[ok] Cleared previous data.")
    
    for i, bug in enumerate(HISTORICAL_BUGS):
        print(f"  Adding Bug #{i+101}...")
        await cognee.remember(data=bug, dataset_name="historical_bugs")

    print(f"\n[ok] Successfully seeded {len(HISTORICAL_BUGS)} historical bugs into Cognee!")
    print("You can now restart your server and the memory queries will be live.")

if __name__ == "__main__":
    asyncio.run(seed())
