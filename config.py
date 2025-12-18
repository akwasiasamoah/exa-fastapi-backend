"""
Configuration module for Exa FastAPI Backend
Manages environment variables and application settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Exa API Configuration
    exa_api_key: str
    
    # Application Configuration
    app_name: str = "Exa FastAPI Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000"
    
    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
