from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from app.core.config import settings

router = APIRouter()

# Initialize Gemini only if API key is provided
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str

@router.post("/generate", response_model=PromptResponse)
async def generate_text(request: PromptRequest):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key is not configured")
        
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(request.prompt)
        return PromptResponse(response=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
