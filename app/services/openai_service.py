"""OpenAI service for image generation."""
import base64
import os
import logging
from typing import Optional

import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for handling OpenAI API calls."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if "OPENAI" in key:
                logger.info(f"Found environment variable: {key}")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Log the first few characters of the API key for debugging
        logger.info(f"API key length: {len(api_key)}")
        logger.info(f"API key starts with: {api_key[:10]}")
        
        # Initialize the client
        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized")
    
    async def generate_illustration(
        self,
        prompt: str,
        size: str = "1536x1024",
        quality: str = "high",
    ) -> Optional[str]:
        """Generate an illustration using OpenAI's GPT-4 Vision model.
        
        Args:
            prompt: The prompt for image generation
            size: The size of the image (default: "1536x1024")
            quality: The quality of the image (default: "high")
            
        Returns:
            Optional[str]: Base64 encoded image data or None if generation fails
        """
        try:
            logger.info(f"Generating illustration with size: {size}, quality: {quality}")
            logger.debug(f"Prompt: {prompt}")
            
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
                quality=quality
            )
            
            # Get the base64 image data
            image_data = response.data[0].b64_json
            logger.info("Successfully generated illustration")
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating illustration: {str(e)}", exc_info=True)
            return None

# Create a singleton instance
openai_service = OpenAIService() 