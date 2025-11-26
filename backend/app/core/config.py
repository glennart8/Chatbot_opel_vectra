# -*- coding: utf-8 -*-
"""
Konfiguration för backend-applikationen
"""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Applikationsinställningar"""

    # App info
    APP_NAME: str = "Husqvarna Motorsåg Chatbot API"
    APP_VERSION: str = "1.0.0"

    # API settings
    API_V1_PREFIX: str = "/api/v1"

    # CORS settings (tillåt requests från frontend)
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Chatbot settings
    MAX_CONTEXT_LENGTH: int = 4000  # Ökad för mer kontext
    NUM_DOCUMENTS: int = 8  # Antal dokument att hämta från FAISS
    MODEL_NAME: str = "google/flan-t5-base"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # Paths (relativa till projektrot)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    # För Docker: kolla om vi kör i container, annars använd lokal path
    FAISS_INDEX_PATH: str = str(Path("/code/faiss_index") if Path("/code").exists() else BASE_DIR / "faiss_index")
    DATA_PATH: str = str(Path("/code/data") if Path("/code").exists() else BASE_DIR / "data")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorera extra variabler i .env

settings = Settings()
