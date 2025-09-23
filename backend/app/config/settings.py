import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra environment variables
    )
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # Google AI Configuration
    google_api_key: str
    
    # fal.ai API Configuration (Seedream v4)
    fal_key: str
    
    # Additional AI Configuration
    nano_banana_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-pro"
    max_concurrent_generations: int = 8  # fal.ai limit: 10 concurrent tasks (safe buffer)
    generation_timeout: int = 300  # 5 minutes
    logo_image_size: int = 2048  # 2048x2048 for logos
    
    # Application Settings
    environment: str = "development"
    debug: bool = True

settings = Settings()