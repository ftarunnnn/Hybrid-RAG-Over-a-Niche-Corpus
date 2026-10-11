"""
Application configuration using Pydantic Settings.
Reads environment variables with production defaults.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Hybrid RAG Networking Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Qdrant Vector DB Settings
    QDRANT_LOCATION: str = "qdrant_storage"  # ":memory:", "./qdrant_storage", or "http://localhost:6333"
    QDRANT_COLLECTION: str = "networking_corpus"
    VECTOR_DIM: int = 384
    
    # BM25 Settings
    BM25_INDEX_PATH: str = "data/bm25_index.pkl"
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    
    # Hybrid Retrieval & RRF
    RRF_K: int = 60
    VECTOR_WEIGHT: float = 1.0
    BM25_WEIGHT: float = 1.0
    TOP_K_CANDIDATES: int = 20
    TOP_K_FINAL: int = 5
    
    # Context Builder
    MAX_CONTEXT_TOKENS: int = 2500
    
    # LLM Generator
    LLM_PROVIDER: str = "auto"
    LLM_MODEL: str = "llama3:latest"
    LLM_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""


settings = Settings()
