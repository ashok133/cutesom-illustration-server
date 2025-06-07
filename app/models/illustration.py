"""Models for illustration generation."""
from typing import Optional
from pydantic import BaseModel, Field

class IllustrationRequest(BaseModel):
    """Request model for illustration generation."""
    
    stanza_text: str = Field(description="The stanza text to illustrate")
    baby_name: str = Field(description="Name of the baby")
    image_number: int = Field(description="Image number in the sequence (1-8)")
    baby_photo_description: Optional[str] = Field(default=None, description="Description of baby's appearance")
    parent1_name: Optional[str] = Field(default=None, description="Name of first parent")
    parent1_photo_description: Optional[str] = Field(default=None, description="Description of first parent's appearance")
    parent2_name: Optional[str] = Field(default=None, description="Name of second parent")
    parent2_photo_description: Optional[str] = Field(default=None, description="Description of second parent's appearance")
    family_member_name: Optional[str] = Field(default=None, description="Name of family member")
    family_member_photo_description: Optional[str] = Field(default=None, description="Description of family member's appearance")

class IllustrationResponse(BaseModel):
    """Response model for illustration generation."""
    
    image_data: str = Field(description="Base64 encoded image data")
    prompt_used: str = Field(description="The prompt used for generation") 