from fastapi import APIRouter, HTTPException
from app.models.illustration import IllustrationRequest, IllustrationResponse
from app.services.openai_service import openai_service
from app.utils.prompt_utils import format_illustration_prompt

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API routing."""
    return {"message": "API is working"}

@router.post("/generate-illustration", response_model=IllustrationResponse)
async def generate_illustration(request: IllustrationRequest):
    """Generate an illustration based on the provided parameters.
    
    Args:
        request: The illustration generation request
        
    Returns:
        IllustrationResponse: The generated illustration data
        
    Raises:
        HTTPException: If illustration generation fails
    """
    # Format the prompt using the template
    prompt = format_illustration_prompt(
        stanza_text=request.stanza_text,
        baby_name=request.baby_name,
        image_number=request.image_number,
        baby_photo_description=request.baby_photo_description,
        parent1_name=request.parent1_name,
        parent1_photo_description=request.parent1_photo_description,
        parent2_name=request.parent2_name,
        parent2_photo_description=request.parent2_photo_description,
        family_member_name=request.family_member_name,
        family_member_photo_description=request.family_member_photo_description
    )
    
    # Generate the illustration
    image_data = await openai_service.generate_illustration(
        prompt=prompt,
        size="1536x1024",  # Match the template requirements
        quality="high",
    )
    
    if not image_data:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate illustration"
        )
    
    return IllustrationResponse(
        image_data=image_data,
        prompt_used=prompt
    ) 