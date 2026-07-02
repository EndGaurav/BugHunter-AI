import asyncio
import json
import httpx
from pydantic import BaseModel

async def test_webhook():
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 104,
            "diff_url": "https://patch-diff.githubusercontent.com/raw/hwchase17/langchain/pull/1.diff"
        },
        "repository": {
            "full_name": "hwchase17/langchain"
        }
    }
    
    headers = {
        "x-github-event": "pull_request"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://127.0.0.1:8000/api/webhook", json=payload, headers=headers, timeout=30.0)
            print(f"Status: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
