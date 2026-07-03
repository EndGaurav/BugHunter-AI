from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hackathon API"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    AWS_BEARER_TOKEN_BEDROCK: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Trigger reload
