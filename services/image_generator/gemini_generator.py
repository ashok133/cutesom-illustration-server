import logging
import os
import io
import base64
import aiohttp
from typing import List, Optional
from google import genai
from google.genai import types
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
            
            # Default to the "Nano Banana Pro" equivalent (Gemini 3 Pro Image Preview)
            # or allow override.
            self.model_name = os.environ.get('GEMINI_MODEL_ID', 'gemini-3-pro-image-preview') 
            
            # Using the new SDK client
            self.client = genai.Client(api_key=api_key)
            logger.info(f"GeminiGenerator initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing GeminiGenerator: {str(e)}")
            raise

    async def _fetch_image(self, url: str) -> Optional[Image.Image]:
        """Fetch an image from a URL or data URI and return as PIL Image."""
        try:
            if url.startswith('data:'):
                # Handle data URI
                try:
                    header, encoded = url.split(',', 1)
                    data = base64.b64decode(encoded)
                    return Image.open(io.BytesIO(data))
                except Exception as e:
                    logger.error(f"Error decoding data URI: {str(e)}")
                    return None
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        return Image.open(io.BytesIO(data))
                    else:
                        logger.error(f"Failed to fetch image from {url}: {response.status}")
                        return None
        except Exception as e:
            # Truncate long data URIs in logs to avoid spam
            log_url = url[:100] + "..." if len(url) > 100 else url
            logger.error(f"Error fetching image {log_url}: {str(e)}")
            return None

    async def generate_illustration(
        self,
        prompt: str,
        reference_images: List[str],

    ) -> Optional[str]:
        """Generate illustration using Gemini / Imagen 3."""
        try:
            logger.info(f"Generating illustration (Gemini: {self.model_name})")
            
            # Fetch reference images
            contents = [prompt]
            if reference_images:
                valid_refs = 0
                for url in reference_images:
                    if img := await self._fetch_image(url):
                        contents.append(img)
                        valid_refs += 1
                logger.info(f"Included {valid_refs} reference images")

            # Generate
            try:
                # Use generate_images for correctness with image generation models
                response = self.client.models.generate_images(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="16:9",
                        ),
                    )
                )
            except Exception as api_error:
                logger.error(f"Gemini API Error: {str(api_error)}")
                return None
            
            # Extract Image
            candidates = getattr(response, 'generated_images', None) or getattr(response, 'candidates', None)
            
            if not candidates:
                logger.warning("No candidates received from Gemini.")
                return None

            for candidate in candidates:
                # Handle 'GeneratedImage' object (from generate_images)
                if hasattr(candidate, 'image') and hasattr(candidate.image, 'image_bytes'):
                    return self._process_image_bytes(candidate.image.image_bytes)
                
                # Handle 'Candidate' object (from generate_content fallback/mix)
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                             return self._process_image_bytes(part.inline_data.data)
            
            logger.error("No valid image data found in response.")
            return None
            
        except Exception as e:
            logger.error(f"Error calling Gemini: {str(e)}", exc_info=True)
            return None

    def _process_image_bytes(self, data: bytes) -> Optional[str]:
        """Validate and convert raw image bytes (or base64 bytes) to a clean base64 string."""
        if not data:
            return None
            
        try:
            # 1. Try treating as raw binary image
            img = Image.open(io.BytesIO(data))
            img.verify()
            img = Image.open(io.BytesIO(data)) # Re-open after verify
        except Exception:
            try:
                # 2. Fallback: Try treating as base64 encoded bytes
                decoded = base64.b64decode(data)
                img = Image.open(io.BytesIO(decoded))
                img.verify()
                img = Image.open(io.BytesIO(decoded))
            except Exception:
                logger.error("Failed to process bytes: neither valid raw image nor base64 image.")
                return None

        # Convert to consistent PNG format
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        logger.info(f"Successfully processed image. Output size: {len(b64_str)} chars")
        return b64_str

