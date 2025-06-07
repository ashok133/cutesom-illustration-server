"""Utility functions for handling prompts."""
import os
from pathlib import Path

def load_prompt_template() -> str:
    """Load the illustration prompt template.
    
    Returns:
        str: The prompt template text
    """
    template_path = Path(__file__).parent.parent / "api" / "v1" / "config" / "illustration_prompt.txt"
    with open(template_path, "r") as f:
        return f.read()

def format_illustration_prompt(
    stanza_text: str,
    baby_name: str,
    image_number: int,
    baby_photo_description: str = None,
    parent1_name: str = None,
    parent1_photo_description: str = None,
    parent2_name: str = None,
    parent2_photo_description: str = None,
    family_member_name: str = None,
    family_member_photo_description: str = None
) -> str:
    """Format the illustration prompt with the provided parameters.
    
    Args:
        stanza_text: The stanza text to illustrate
        baby_name: Name of the baby
        image_number: Image number in the sequence (1-8)
        baby_photo_description: Description of baby's appearance
        parent1_name: Name of first parent
        parent1_photo_description: Description of first parent's appearance
        parent2_name: Name of second parent
        parent2_photo_description: Description of second parent's appearance
        family_member_name: Name of family member
        family_member_photo_description: Description of family member's appearance
        
    Returns:
        str: The formatted prompt
    """
    template = load_prompt_template()
    
    # Replace basic placeholders
    prompt = template.replace("[STANZA_TEXT]", stanza_text)
    prompt = prompt.replace("[baby_name]", baby_name)
    prompt = prompt.replace("[image_number]", str(image_number))
    
    # Handle optional character descriptions
    if baby_photo_description:
        prompt = prompt.replace("[baby_photo_description]", baby_photo_description)
    else:
        prompt = prompt.replace("If [baby_name] appears: [baby_photo_description]", "")
    
    if parent1_name and parent1_photo_description:
        prompt = prompt.replace("[parent1_name]", parent1_name)
        prompt = prompt.replace("[parent1_photo_description]", parent1_photo_description)
    else:
        prompt = prompt.replace("If [parent1_name] appears: [parent1_photo_description]", "")
    
    if parent2_name and parent2_photo_description:
        prompt = prompt.replace("[parent2_name]", parent2_name)
        prompt = prompt.replace("[parent2_photo_description]", parent2_photo_description)
    else:
        prompt = prompt.replace("If [parent2_name] appears: [parent2_photo_description]", "")
    
    if family_member_name and family_member_photo_description:
        prompt = prompt.replace("[family_member_name]", family_member_name)
        prompt = prompt.replace("[family_member_photo_description]", family_member_photo_description)
    else:
        prompt = prompt.replace("If [family_member_name] appears: [family_member_photo_description]", "")
    
    # Clean up any double newlines that might have been created
    prompt = "\n".join(line for line in prompt.split("\n") if line.strip())
    
    return prompt 