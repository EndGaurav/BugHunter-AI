from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
from app.core.config import settings

from app.api.webhook import router as webhook_router

router = APIRouter()
router.include_router(webhook_router)

# Initialize Groq only if API key is provided
client = None
if settings.GROQ_API_KEY:
    client = Groq(api_key=settings.GROQ_API_KEY)
    
class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str

@router.post("/generate", response_model=PromptResponse)
async def generate_text(request: PromptRequest):
    if not settings.GROQ_API_KEY or not client:
        raise HTTPException(status_code=500, detail="Groq API key is not configured")
        
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": request.prompt}],
        )
        return PromptResponse(response=response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
