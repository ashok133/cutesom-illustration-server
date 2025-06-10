"""Test script for OpenAI image generation with reference images."""
import os
import base64
import logging
from typing import List
from openai import OpenAI
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_base64_images_from_folder(folder_path: str) -> List[str]:
    """Load all PNG image files in the given folder and return a list of base64-encoded strings.
    
    Args:
        folder_path: Path to the folder containing image files.
        
    Returns:
        List[str]: List of base64 encoded image data strings with data URI prefix.
    """
    base64_images = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith('.png'):
            try:
                with open(file_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    data_uri = f"data:image/png;base64,{encoded}"
                    base64_images.append(data_uri)
            except Exception as e:
                logger.error(f"Error encoding image {file_path}: {str(e)}")
    return base64_images

def generate_illustration(
    prompt: str,
    size: str = "1536x1024",
    quality: str = "high",
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> str:
    """Generate an illustration using OpenAI's GPT-4 Vision model.
    
    Args:
        prompt: The prompt for image generation
        size: The size of the image (default: "1536x1024")
        quality: The quality of the image (default: "high")
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)
        
    Returns:
        str: Base64 encoded generated image
    """
    for attempt in range(max_retries):
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Log request details
            logger.info(f"Generating illustration with size: {size}, quality: {quality}")
            logger.debug(f"Prompt: {prompt}")
            
            # Get reference images
            reference_images = get_base64_images_from_folder("tests/test_images")
            logger.info(f"Using {len(reference_images)} reference images")
            
            # Prepare the request
            response = client.responses.create(
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
                                for base64_img in reference_images
                            ]
                        ]
                    }
                ]
            )
            
            # Log response details
            logger.info("Successfully generated illustration")
            
            # Extract base64 string from response
            for output in response.output:
                if hasattr(output, 'result') and output.result:
                    # Save the base64 string to a file
                    with open("response.txt", "w") as f:
                        f.write(str(response))
                    
                    # Save the image
                    image_data = output.result
                    output_path = "generated_illustration.png"
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(image_data))
                    logger.info(f"Saved generated image to: {output_path}")
                    return image_data
            
            # If we get here, no image data was found
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"No image data found in response. Retrying in {delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
                
            raise ValueError("No image data found in response after all retries")
            
        except Exception as e:
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.warning(f"Error generating illustration: {str(e)}. Retrying in {delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
            logger.error(f"Error generating illustration after {max_retries} attempts: {str(e)}", exc_info=True)
            raise

def main():
    """Main function to test image generation."""
    prompt = "Create a watercolor-style children's book illustration of a baby playing with toys in a sunny room"
    
    try:
        # Generate illustration
        image_data = generate_illustration(prompt=prompt)
        
        # Save the generated image
        output_path = "generated_illustration.jpg"
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_data))
        logger.info(f"Saved generated image to: {output_path}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 