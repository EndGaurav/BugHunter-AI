from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router as api_router
from app.core.config import settings
from app.core.cognee_config import setup_cognee

@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_cognee()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API with Gemini integration",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hackathon API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
