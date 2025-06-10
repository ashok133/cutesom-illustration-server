"""Test script for the illustration generation service."""
import base64
import json
import logging
import os
from pathlib import Path
import requests
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service configuration
SERVICE_URL = "https://cutesom-illustration-server-241564477458.us-central1.run.app"
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
OUTPUT_DIR = Path(__file__).parent / "output"
TEST_USER_EMAIL = "ashok-test@example.com"  # Test user email

def ensure_directories():
    """Ensure test and output directories exist."""
    TEST_IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

def load_image_as_base64(image_path: Path) -> str:
    """Load an image file and convert it to base64."""
    try:
        with open(image_path, "rb") as image_file:
            base64_data = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
    except Exception as e:
        logger.error(f"Error loading image {image_path}: {str(e)}")
        return ""

def create_test_request() -> Dict[str, Any]:
    """Create a test request payload."""
    # Sample poem with multiple stanzas
    poem = """Little star so bright and true,
Shining in the sky so blue.
Twinkling like a diamond bright,
Making everything just right.
"""

    # Minimal placeholder base64 string (1x1 transparent pixel)
    placeholder_photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    # Create request payload
    request = {
        "poem_text": poem,
        "baby": {
            "name": "Baby Emma",
            "age": "2 years",
            "characteristics": "Curious and playful, loves music and dancing",
            "photo": placeholder_photo
        },
        "parents": {
            "parent1": {
                "name": "Sarah",
                "relationship": "Mother",
                "photo": placeholder_photo
            },
            "parent2": {
                "name": "John",
                "relationship": "Father",
                "photo": placeholder_photo
            }
        },
        "family_members": [
            {
                "name": "Grandma Mary",
                "relationship": "Maternal grandmother",
                "photo": placeholder_photo
            }
        ]
    }
    return request

def save_raw_response(response_data: Dict[str, Any]):
    """Save the raw response data to a JSON file."""
    try:
        output_path = OUTPUT_DIR / "raw_response.json"
        with open(output_path, "w") as f:
            json.dump(response_data, f, indent=2)
        logger.info(f"Saved raw response to {output_path}")
    except Exception as e:
        logger.error(f"Error saving raw response: {str(e)}")

def save_generated_images(response_data: Dict[str, Any]):
    """Save generated images from the response."""
    try:
        # Get image_data from response
        image_data = response_data.get("image_data", {})
        if not image_data:
            logger.error("No image_data found in response")
            return

        for stanza_num, image_data in image_data.items():
            # Remove data URI prefix if present
            if image_data.startswith("data:image/jpeg;base64,"):
                image_data = image_data.replace("data:image/jpeg;base64,", "")
            
            # Decode base64 image
            try:
                image_bytes = base64.b64decode(image_data)
            except Exception as e:
                logger.error(f"Error decoding base64 for stanza {stanza_num}: {str(e)}")
                continue
            
            # Save image
            output_path = OUTPUT_DIR / f"stanza_{stanza_num}.jpg"
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Saved image for stanza {stanza_num} to {output_path}")
    except Exception as e:
        logger.error(f"Error saving generated images: {str(e)}")

def test_illustration_generation():
    """Test the illustration generation endpoint."""
    try:
        # Ensure directories exist
        ensure_directories()
        
        # Create test request
        request_data = create_test_request()
        
        # Make API request
        logger.info(f"Sending request to illustration service at {SERVICE_URL}...")
        response = requests.post(
            f"{SERVICE_URL}/generate-illustration",
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "user-email": TEST_USER_EMAIL
            }
        )
        
        # Check response
        response.raise_for_status()
        response_data = response.json()
        
        # Log response status and message
        logger.info(f"Response status: {response_data.get('status')}")
        logger.info(f"Response message: {response_data.get('message')}")
        
        # Save raw response
        save_raw_response(response_data)
        
        # Save generated images
        save_generated_images(response_data)
        
        return response_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to service: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response text: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

if __name__ == "__main__":
    test_illustration_generation() 