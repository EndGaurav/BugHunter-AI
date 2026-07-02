"""
Cognee memory inspector - dekho kya bugs stored hain.
Usage: uv run python inspect_memory.py
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY", "")

# Cognee env vars set karo BEFORE import
os.environ["LLM_API_KEY"] = groq_api_key
os.environ["LLM_MODEL"] = "groq/llama-3.3-70b-versatile"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["EMBEDDING_PROVIDER"] = "fastembed"
os.environ["GRAPH_DATABASE_PROVIDER"] = "ladybug"
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"
os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"

import cognee

async def inspect():
    print("\n" + "="*60)
    print("  COGNEE MEMORY INSPECTOR")
    print("="*60)

    # Apna query yahan likho
    queries = [
        "webhook bugs",
        "race condition",
        "diff parsing",
        "authentication issues",
    ]

    for q in queries:
        print(f"\n  Query: '{q}'")
        print("-"*40)
        try:
            results = await cognee.recall(q)
            if results:
                for item in results:
                    print(f"  -> {str(item)[:200]}")
            else:
                print("  (no results found)")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(inspect())
