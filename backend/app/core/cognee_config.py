import os
import cognee
import logging
import litellm

logger = logging.getLogger(__name__)

async def setup_cognee():
    # drop unsupported params for bedrock in litellm
    litellm.drop_params = True
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

        # LLM: route through LiteLLM to AWS Bedrock
        bedrock_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "dummy-key")
        cognee.config.set_llm_provider("openai")
        cognee.config.set_llm_model("bedrock/meta.llama3-8b-instruct-v1:0")
        cognee.config.set_llm_api_key(bedrock_token)
        
        if hasattr(cognee.config, "set_llm_endpoint"):
            cognee.config.set_llm_endpoint(None)
            
        # No need to set openai base URL since litellm handles Bedrock natively
        if "OPENAI_BASE_URL" in os.environ:
            del os.environ["OPENAI_BASE_URL"]
            
        # LiteLLM needs the AWS region to construct the bedrock endpoint URL correctly
        os.environ["AWS_REGION_NAME"] = "us-east-1"

        print("Cognee has been successfully configured with Graph and Vector memory.")
        logger.info("Cognee has been successfully configured with Graph and Vector memory.")
    except Exception as e:
        logger.error(f"Failed to configure Cognee: {e}")
        raise
