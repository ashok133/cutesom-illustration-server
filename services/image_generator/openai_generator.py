import logging
import os
from typing import List, Optional
from openai import OpenAI
from .base import ImageGenerator

logger = logging.getLogger(__name__)

class OpenAIGenerator(ImageGenerator):
    """OpenAI implementation of the ImageGenerator."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        try:
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                # We log a warning instead of raising, in case only other providers are used
                logger.warning("OPENAI_API_KEY not set. OpenAIGenerator will fail if used.")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.openai.com/v1"
            )
            logger.info("OpenAIGenerator initialized")
            
        except Exception as e:
            logger.error(f"Error initializing OpenAIGenerator: {str(e)}")
            raise

    async def generate_illustration(
        self,
        prompt: str,
        reference_images: List[str],
        size: str = "1536x1024",
        quality: str = "high",
    ) -> Optional[str]:
        """Generate illustration using OpenAI DALL-E 3 / GPT-4 Vision."""
        try:
            logger.info(f"Generating illustration (OpenAI) size: {size}, quality: {quality}")
            
            response = self.client.responses.create(
                model="gpt-4.1", # Keeping the model from original code
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
            
            for output in response.output:
                if hasattr(output, 'result') and output.result:
                    res = output.result
                    if isinstance(res, str):
                        logger.info(f"OpenAI generated image size: {len(res)} chars")
                    return res
                    
            logger.error("No image data found in OpenAI response")
            return None
            
        except Exception as e:
            logger.error(f"Error calling OpenAI: {str(e)}", exc_info=True)
            return None
