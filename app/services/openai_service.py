"""OpenAI service for image generation."""
import base64
import os
import logging
from typing import Optional, List
from PIL import Image
import io

import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for handling OpenAI API calls."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        try:
            # Get API key from environment variable
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            logger.info("Successfully retrieved API key from environment")
            
            # Initialize the client with just the API key
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.openai.com/v1"
            )
            logger.info("OpenAI client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing OpenAI service: {str(e)}")
            raise
    
    async def generate_illustration(
        self,
        prompt: str,
        reference_images: List[str],
        size: str = "1536x1024",
        quality: str = "high",
    ) -> Optional[str]:
        """Generate an illustration using OpenAI's GPT-4 Vision model.
        
        Args:
            prompt: The prompt for image generation
            reference_images: List of image URLs (from Cloud Storage)
            size: The size of the image (default: "1536x1024")
            quality: The quality of the image (default: "high")
            
        Returns:
            Optional[str]: Base64 encoded image data or None if generation fails
        """
        try:
            logger.info(f"Generating illustration with size: {size}, quality: {quality}")
            logger.debug(f"Prompt: {prompt}")
            logger.info(f"Using {len(reference_images)} reference images")
            
            response = self.client.responses.create(
                model="gpt-4.1",
                tools=[{"type": "image_generation"}],
                input=[
                    {
                        "role": "system",
                        "content": "You are an expert children's book illustrator. Use the following input to generate a watercolor-style storybook image."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            },
                            *[
                                {
                                    "type": "input_image",
                                    "image_url": image_url,
                                    "detail": "auto"
                                }
                                for image_url in reference_images
                            ]
                        ]
                    }
                ]
            )
            
            # Extract base64 string from response
            for output in response.output:
                if hasattr(output, 'result') and output.result:
                    logger.info("Successfully generated illustration")
                    return output.result
                    
            logger.error("No image data found in response")
            return None
            
        except Exception as e:
            logger.error(f"Error generating illustration: {str(e)}", exc_info=True)
            return None

# Create a singleton instance
openai_service = OpenAIService() 