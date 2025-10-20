"""
Application configuration settings
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Application settings
    app_name: str = "AURELIA RAG Service"
    environment: str = "development"
    debug: bool = True
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # Vector Store settings
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "fintbx-embeddings"  # Lab 1 index
    
    # LLM settings
    openai_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    
    # Embedding settings
    embedding_model: str = "text-embedding-3-large"  # OpenAI model
    embedding_dimension: int = 3072  # text-embedding-3-large dimensions
    
    # RAG settings
    default_top_k: int = 5
    max_top_k: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from parent .env files


# Create settings instance
settings = Settings()

