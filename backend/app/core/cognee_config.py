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
        cognee.config.set_graph_db_provider("networkx")
        
        # We can also configure the LLM provider here if needed
        # e.g., cognee.config.set_llm_provider("gemini")
        
        logger.info("Cognee has been successfully configured with Graph and Vector memory.")
    except Exception as e:
        logger.error(f"Failed to configure Cognee: {e}")
        raise
