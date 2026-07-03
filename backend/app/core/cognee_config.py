import os
import cognee
import logging

logger = logging.getLogger(__name__)

async def setup_cognee():
    """
    Configures Cognee to handle both graph (code dependencies) and vector (past bugs) memory.
    Through its unified interface.
    """
    try:
        # Vector database for semantic search (past bugs)
        cognee.config.set_vector_db_provider("lancedb")

        # Graph database for relationships (code dependencies)
        cognee.config.set_graph_database_provider("ladybug")

        # Embedding: use local fastembed (no API key needed)
        cognee.config.set_embedding_provider("fastembed")
        cognee.config.set_embedding_model("sentence-transformers/all-MiniLM-L6-v2")

        # LLM: route through LiteLLM to Groq using openai-compatible interface
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        cognee.config.set_llm_provider("openai")
        cognee.config.set_llm_model("groq/llama-3.3-70b-versatile")
        cognee.config.set_llm_api_key(groq_api_key)

        print("Cognee has been successfully configured with Graph and Vector memory.")
        logger.info("Cognee has been successfully configured with Graph and Vector memory.")
    except Exception as e:
        logger.error(f"Failed to configure Cognee: {e}")
        raise
