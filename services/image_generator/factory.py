import os
import logging
from .base import ImageGenerator
from .openai_generator import OpenAIGenerator
from .gemini_generator import GeminiGenerator

logger = logging.getLogger(__name__)

def get_image_generator(model_alias: str = "gpt-image") -> ImageGenerator:
    """Factory function to get the configured image generator.
    
    Args:
        model_alias: The alias of the model to use ('nano-banana' or 'gpt-image').
    """
    # Normalize input
    alias = model_alias.lower()
    
    if alias == 'nano-banana':
        logger.info("Using Gemini Image Generator (Nano Banana)")
        return GeminiGenerator()
    elif alias == 'gpt-image':
        logger.info("Using OpenAI Image Generator")
        return OpenAIGenerator()
    else:
        logger.warning(f"Unknown model alias '{model_alias}', falling back to OpenAI")
        return OpenAIGenerator()
