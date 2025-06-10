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
    
    def _preprocess_image(self, image_data: str, max_size: int = 512, quality: int = 85) -> str:
        """Preprocess image to reduce size while maintaining quality.
        
        Args:
            image_data: Base64 encoded image data with data URI prefix
            max_size: Maximum dimension (width or height) in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            str: Base64 encoded preprocessed image with data URI prefix
        """
        try:
            # Remove data URI prefix if present
            if image_data.startswith('data:image/jpeg;base64,'):
                image_data = image_data.replace('data:image/jpeg;base64,', '')
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)
            
            # Open image from bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new dimensions while maintaining aspect ratio
            ratio = min(max_size / max(img.size), 1.0)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            
            # Resize image
            if ratio < 1.0:
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to bytes with compression
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Convert to base64
            encoded = base64.b64encode(output.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded}"
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            # Return original image if preprocessing fails
            return image_data
    
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
            reference_images: List of base64 encoded images with data URI prefix
            size: The size of the image (default: "1536x1024")
            quality: The quality of the image (default: "high")
            
        Returns:
            Optional[str]: Base64 encoded image data or None if generation fails
        """
        try:
            logger.info(f"Generating illustration with size: {size}, quality: {quality}")
            logger.debug(f"Prompt: {prompt}")
            
            # Preprocess reference images
            processed_images = [
                self._preprocess_image(img_data)
                for img_data in reference_images
            ]
            logger.info(f"Processed {len(processed_images)} reference images")
            
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
                                    "image_url": base64_img,
                                    "detail": "auto"
                                }
                                for base64_img in processed_images
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