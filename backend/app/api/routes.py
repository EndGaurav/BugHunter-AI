from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from app.core.config import settings

from app.api.webhook import router as webhook_router

router = APIRouter()
router.include_router(webhook_router)

# Initialize OpenAI for Bedrock only if API key is provided
client = None
if settings.AWS_BEARER_TOKEN_BEDROCK:
    client = OpenAI(
        api_key=settings.AWS_BEARER_TOKEN_BEDROCK,
        base_url="https://bedrock-runtime.us-east-1.amazonaws.com/v1"
    )
    
class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str

@router.post("/generate", response_model=PromptResponse)
async def generate_text(request: PromptRequest):
    if not settings.AWS_BEARER_TOKEN_BEDROCK or not client:
        raise HTTPException(status_code=500, detail="AWS Bedrock API key is not configured")
        
    try:
        response = client.chat.completions.create(
            model="meta.llama3-8b-instruct-v1:0",
            messages=[{"role": "user", "content": request.prompt}],
        )
        return PromptResponse(response=response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
