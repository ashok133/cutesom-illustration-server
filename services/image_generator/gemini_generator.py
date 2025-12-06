import logging
import os
import io
import base64
import aiohttp
from typing import List, Optional
import google.generativeai as genai
from PIL import Image
from .base import ImageGenerator

logger = logging.getLogger(__name__)

class GeminiGenerator(ImageGenerator):
    """Gemini implementation of the ImageGenerator using Imagen 3."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        try:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                logger.warning("GEMINI_API_KEY not set. GeminiGenerator will fail if used.")
            else:
                genai.configure(api_key=api_key)
            
            # Default to the "Nano Banana Pro" equivalent (Gemini 3 Pro Image Preview)
            # or allow override.
            self.model_name = os.environ.get('GEMINI_MODEL_ID', 'gemini-3-pro-preview-image') 
            self.client = genai.Client(api_key=api_key)
            logger.info(f"GeminiGenerator initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing GeminiGenerator: {str(e)}")
            raise

    async def _fetch_image(self, url: str) -> Optional[Image.Image]:
        """Fetch an image from a URL and return as PIL Image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        return Image.open(io.BytesIO(data))
                    else:
                        logger.error(f"Failed to fetch image from {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching image {url}: {str(e)}")
            return None

    async def generate_illustration(
        self,
        prompt: str,
        reference_images: List[str],
        size: str = "1024x1024", 
        quality: str = "standard",
    ) -> Optional[str]:
        """Generate illustration using Gemini / Imagen 3."""
        try:
            logger.info(f"Generating illustration (Gemini: {self.model_name})")
            
            # 1. Fetch reference images if any
            pil_reference_images = []
            if reference_images:
                logger.info(f"Fetching {len(reference_images)} reference images...")
                for url in reference_images:
                    img = await self._fetch_image(url)
                    if img:
                        pil_reference_images.append(img)
            
            # 2. Construct content
            # The SDK for Imagen 3 via generate_content expects [prompt, image1, image2, ...]
            contents = [prompt]
            contents.extend(pil_reference_images)

            # 3. Configure generation
            # Note: Aspect ratio is often inferred or set via config. 
            # 'size' param string might need parsing if strict control is needed, 
            # but Imagen often handles '1:1', '3:4', etc. better than raw pixels.
            # For now, we rely on the model's default or prompt instructions for size.
            
            # 4. Generate
            # We use the client.models.generate_content method as seen in docs
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    response_modalities=["IMAGE"] # Force image output
                )
            )
            
            # 5. Process Response
            # The response should contain parts with inline_data (bytes)
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    # Convert bytes to base64 string
                    image_bytes = part.inline_data.data
                    base64_image = base64.b64encode(image_bytes).decode('utf-8')
                    return base64_image
            
            logger.error("No image data found in Gemini response")
            return None
            
        except Exception as e:
            logger.error(f"Error calling Gemini: {str(e)}", exc_info=True)
            return None
