"""Configuration settings for the application."""
import os
from functools import lru_cache
from typing import Optional

from google.cloud import secretmanager
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Cutesom Illustration Server"
    PROJECT_ID: str = os.getenv("PROJECT_ID", "")
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_secret(secret_id: str, version_id: str = "latest") -> Optional[str]:
    """Get a secret from Google Cloud Secret Manager.
    
    Args:
        secret_id: The ID of the secret to retrieve
        version_id: The version of the secret to retrieve (default: "latest")
        
    Returns:
        Optional[str]: The secret value or None if not found
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{get_settings().PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret {secret_id}: {str(e)}")
        return None


# Create a global settings instance
settings = get_settings()