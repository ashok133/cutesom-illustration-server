#!/usr/bin/env python3

import json
import requests
from datetime import datetime
import os

def generate_test_image():
    # Create timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tests/images/illustration_{timestamp}.txt"
    usage_file = f"tests/images/usage_{timestamp}.json"
    debug_file = f"tests/images/debug_response_{timestamp}.json"

    # Ensure the images directory exists
    os.makedirs("tests/images", exist_ok=True)

    # API request payload
    payload = {
        "stanza_text": "In a cozy nursery filled with toys and light, little Emma giggles with pure delight. Her tiny hands reach up to touch the mobile above, while her parents watch with endless love.",
        "baby_name": "Emma",
        "image_number": 1,
        "baby_photo_description": "A 6-month-old baby with rosy cheeks, bright blue eyes, and soft golden curls. She has a small birthmark on her left cheek and a sweet, dimpled smile.",
        "parent1_name": "Sarah",
        "parent1_photo_description": "A young mother with warm brown eyes, long auburn hair in a loose braid, and a gentle smile. She has fair skin with freckles across her nose.",
        "parent2_name": "Michael",
        "parent2_photo_description": "A tall father with kind hazel eyes, short dark brown hair with a touch of gray at the temples, and a friendly face. He has olive skin and a neatly trimmed beard.",
        "family_member_name": "Grandma Rose",
        "family_member_photo_description": "An elderly woman with silver-white hair in a neat bun, twinkling blue eyes behind round glasses, and a warm smile. She has fair skin with gentle wrinkles and always wears a pearl necklace."
    }

    try:
        # Make the API request
        response = requests.post(
            "http://localhost:8000/api/v1/generate-illustration",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Save the full response for debugging
        with open(debug_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Debug response saved to: {debug_file}")

        # Check if we have the expected structure
        if "image_data" not in data:
            print("Error: Response does not contain 'image_data' field")
            print("Response structure:", json.dumps(data, indent=2))
            return

        # Save the base64 string
        with open(output_file, "w") as f:
            f.write(data["image_data"])

        # Save the prompt used if available
        if "prompt_used" in data:
            prompt_file = f"tests/images/prompt_{timestamp}.txt"
            with open(prompt_file, "w") as f:
                f.write(data["prompt_used"])
            print(f"Prompt saved to: {prompt_file}")

        print(f"Image saved to: {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    generate_test_image() 