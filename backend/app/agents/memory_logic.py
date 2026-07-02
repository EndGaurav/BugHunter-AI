import cognee
import logging

logger = logging.getLogger(__name__)

async def retrieve_context(parsed_files: dict) -> str:
    """
    Queries Cognee's memory for context relevant to the PR's changed files.
    - Searches the vector store for semantically similar past bugs.
    """
    filenames = list(parsed_files.keys())
    logger.info(f"Querying Cognee memory for files: {filenames}")

    if not filenames:
        return "No files were changed, so no memory context was retrieved."

    try:
        # Build a natural language query from the changed filenames
        query = f"What historical bugs or issues are related to changes in these files: {', '.join(filenames)}?"

        # Use Cognee's recall to semantically search the memory
        results = await cognee.recall(query)

        if not results:
            logger.info("Cognee returned no relevant historical context.")
            return "No relevant historical bugs or context found in memory for this change."

        # Format the results into a readable string for the LLM prompt
        context_lines = ["HISTORICAL CONTEXT FROM MEMORY:"]
        if isinstance(results, list):
            for item in results:
                context_lines.append(f"- {str(item)}")
        else:
            context_lines.append(str(results))

        return "\n".join(context_lines)

    except Exception as e:
        logger.error(f"Error querying Cognee: {e}")
        return f"Memory retrieval encountered an error: {e}. Proceeding without historical context."

