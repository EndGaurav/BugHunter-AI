import httpx
import logging

logger = logging.getLogger(__name__)

async def extract_pr_diff(diff_url: str) -> str:
    """
    Fetches the raw PR diff from a given GitHub diff URL.
    """
    # Using follow_redirects=True as GitHub sometimes redirects diff URLs
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(diff_url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error fetching PR diff: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching PR diff: {e}")
            raise

def parse_modified_code(raw_diff: str) -> dict:
    """
    Parses a raw git diff and extracts modified files and their code changes.
    Returns a dictionary mapping filenames to their respective diff content.
    """
    files = {}
    current_file = None
    current_content = []
    
    for line in raw_diff.splitlines():
        if line.startswith("diff --git"):
            # Save the previous file's diff
            if current_file:
                files[current_file] = "\n".join(current_content)
            
            # Extract filename from 'diff --git a/filename b/filename'
            parts = line.split(" ")
            if len(parts) >= 4:
                # Remove the 'b/' prefix from the target filename
                current_file = parts[3][2:] if parts[3].startswith("b/") else parts[3]
            else:
                current_file = "unknown"
                
            current_content = [line]
        else:
            if current_file:
                current_content.append(line)
                
    # Don't forget the last file
    if current_file and current_content:
        files[current_file] = "\n".join(current_content)
        
    return files
