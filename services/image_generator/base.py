from abc import ABC, abstractmethod
from typing import List, Optional

class ImageGenerator(ABC):
    """Abstract base class for image generation services."""

    @abstractmethod
    async def generate_illustration(
        self,
        prompt: str,
        reference_images: List[str],
        size: str = "1024x1024",
        quality: str = "standard",
    ) -> Optional[str]:
        """Generate an illustration based on the prompt and reference images.
        
        Args:
            prompt: The text prompt for generation.
            reference_images: List of reference image URLs (or base64 if supported).
            size: Target size string (e.g., "1024x1024").
            quality: Quality setting (e.g., "standard", "high").
            
        Returns:
            Optional[str]: Base64 encoded image data or None if failed.
        """
        pass
