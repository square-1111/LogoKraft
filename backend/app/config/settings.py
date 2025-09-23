import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # Google AI Configuration
    google_api_key: str
    
    # Image Generation APIs (optional for now)
    seedream_api_key: Optional[str] = None
    nano_banana_api_key: Optional[str] = None
    
    # Application Settings
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()