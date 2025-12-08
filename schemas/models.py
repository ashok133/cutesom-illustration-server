"""Pydantic models for request and response schemas."""
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class Person(BaseModel):
    """Base model for a person with photo."""
    name: str = Field(..., description="Name of the person")
    photo: str = Field(..., description="Base64 encoded photo of the person or URL")

class Baby(Person):
    """Model for baby information."""
    age: str = Field(..., description="Age of the baby (e.g., '2 years old', '6 months')")
    characteristics: Optional[str] = Field(None, description="Physical characteristics or notable features of the baby")

class Parent(Person):
    """Model for parent information."""
    relationship: str = Field(..., description="Relationship to the baby (e.g., 'mother', 'father')")

class Parents(BaseModel):
    """Model for parents information."""
    parent1: Optional[Parent] = Field(None, description="First parent")
    parent2: Optional[Parent] = Field(None, description="Second parent")

class FamilyMember(Person):
    """Model for family member information."""
    relationship: str = Field(..., description="Relationship to the baby (e.g., 'grandmother', 'uncle')")

class IllustrationRequest(BaseModel):
    """Model for illustration generation request."""
    poem_text: str = Field(..., description="The poem text to be illustrated")
    baby: Baby = Field(..., description="Information about the baby")
    parents: Optional[Parents] = Field(None, description="Information about the parents")
    family_members: Optional[List[FamilyMember]] = Field(None, description="List of family members to include")
    style: str = Field(..., description="Illustration style: textured-watercolor, bold-and-bright, abstract, whimsical, or muted")
    image_model: str = Field("gpt-image", description="Model to use: 'nano-banana' or 'gpt-image'")

class IllustrationResponse(BaseModel):
    """Model for illustration generation response."""
    status: str = Field(..., description="Status of the request ('success' or 'error')")
    message: str = Field(..., description="Response message")
    image_data: Optional[Dict[str, str]] = Field(
        None, 
        description="Dictionary mapping stanza numbers to base64 encoded illustrations"
    )
    cover_image: Optional[str] = Field(
        None,
        description="Base64 encoded storybook cover image"
    )
    error: Optional[str] = Field(None, description="Error message if status is 'error'")

class StorybookIllustration(BaseModel):
    """Model for a generated illustration in a storybook."""
    stanzaNumber: int
    imageUrl: str
    prompt: str
    createdAt: datetime

class StorybookSummary(BaseModel):
    """Summary model for a storybook."""
    id: str
    userId: str
    createdAt: datetime
    status: str
    coverUrl: Optional[str] = None

class StorybookDetail(StorybookSummary):
    """Detailed model for a storybook including request and illustrations."""
    request: IllustrationRequest
    illustrations: List[StorybookIllustration]
    error: Optional[str] = None
