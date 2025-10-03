"""
Configuration settings for GetGSA application
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str = "dummy-key-for-development"
    OPENAI_ASSISTANT_ID: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./gsa.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Configuration
    MAX_DOCUMENT_SIZE_MB: int = 2
    MAX_DOCUMENTS_PER_REQUEST: int = 20
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Development
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate OpenAI API key
        if self.OPENAI_API_KEY == "dummy-key-for-development":
            print("⚠️  WARNING: Using dummy OpenAI API key!")
            print("   Please set OPENAI_API_KEY in backend/.env file")
            print("   The server will start but AI features won't work.")

# Global settings instance
settings = Settings()
