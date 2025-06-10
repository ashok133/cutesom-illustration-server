"""Main FastAPI application."""
import logging
import asyncio
import os
from typing import List, Dict, Set
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.services.openai_service import openai_service
from app.services.firebase_service import firebase_service
from app.schemas.models import IllustrationRequest, IllustrationResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Cutesom Illustration Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://cutesom.com",    # Production domain
        "https://*.cutesom.com"   # Subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

async def get_current_user(user_email: str = Header(..., description="User's email address")):
    """Get or create user from Firestore.
    
    Args:
        user_email: User's email address from header
        
    Returns:
        User ID
    """
    try:
        # Create user data from email
        user_data = {
            'uid': user_email,
            'email': user_email
        }
        
        # Create or update user in Firestore
        user_id = await firebase_service.create_user(user_data)
        logger.info(f"User {user_email} found or created in Firestore database 'illustration-server' (auth handled on frontend)")
        return user_id
        
    except Exception as e:
        logger.error(f"Error authenticating user in Firestore: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

def load_prompt_template() -> str:
    """Load the prompt template from file."""
    try:
        prompt_path = os.path.join("app", "api", "v1", "config", "illustration_prompt.txt")
        with open(prompt_path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading prompt template: {str(e)}")
        raise

def split_poem_into_stanzas(poem_text: str) -> List[str]:
    """Split poem text into stanzas.
    
    Args:
        poem_text: The complete poem text
        
    Returns:
        List of stanzas
    """
    # Split by double newlines to separate stanzas
    stanzas = [stanza.strip() for stanza in poem_text.split('\n\n') if stanza.strip()]
    return stanzas

def get_names_in_stanza(stanza: str, names: List[str]) -> Set[str]:
    """Check which names appear in the stanza text.
    
    Args:
        stanza: The stanza text to check
        names: List of names to look for
        
    Returns:
        Set of names that appear in the stanza
    """
    stanza_lower = stanza.lower()
    return {name for name in names if name.lower() in stanza_lower}

async def generate_illustration_for_stanza(
    stanza: str,
    stanza_number: int,
    request: IllustrationRequest,
    total_stanzas: int
) -> str:
    """Generate an illustration for a specific stanza.
    
    Args:
        stanza: The stanza text
        stanza_number: The stanza number (1-based)
        request: The original illustration request
        total_stanzas: Total number of stanzas
        
    Returns:
        Base64 encoded generated image
    """
    try:
        # Extract data from request
        baby_name = request.baby.name
        baby_age = request.baby.age
        baby_characteristics = request.baby.characteristics or ""
        baby_photo = request.baby.photo
        
        # Initialize lists for names and photos
        parent_names = []
        parent_photos = []
        family_member_names = []
        family_member_photos = []
        
        # Process parents if available
        parent_requirements = "No parents included in the illustration."
        if request.parents:
            if request.parents.parent1 and request.parents.parent1.name:
                parent_names.append(request.parents.parent1.name)
                if request.parents.parent1.photo:
                    parent_photos.append(request.parents.parent1.photo)
            if request.parents.parent2 and request.parents.parent2.name:
                parent_names.append(request.parents.parent2.name)
                if request.parents.parent2.photo:
                    parent_photos.append(request.parents.parent2.photo)
        
        # Process family members if available
        family_member_requirements = "No family members included in the illustration."
        if request.family_members:
            for member in request.family_members:
                if member.name:
                    family_member_names.append(member.name)
                    if member.photo:
                        family_member_photos.append(member.photo)
        
        # Get names that appear in this stanza
        stanza_parent_names = get_names_in_stanza(stanza, parent_names)
        stanza_family_names = get_names_in_stanza(stanza, family_member_names)
        
        # Filter photos to only include those of characters in the stanza
        relevant_parent_photos = [
            photo for name, photo in zip(parent_names, parent_photos)
            if name in stanza_parent_names
        ]
        relevant_family_photos = [
            photo for name, photo in zip(family_member_names, family_member_photos)
            if name in stanza_family_names
        ]
        
        # Update requirements based on who appears in the stanza
        if stanza_parent_names:
            parent_names_list = list(stanza_parent_names)  # Convert set to list
            if len(parent_names_list) == 1:
                parent_requirements = f"Include {parent_names_list[0]} and use their photo as reference for accurate appearance."
            else:
                parent_requirements = f"Include {', '.join(parent_names_list[:-1])} and {parent_names_list[-1]}, using their photos as reference for accurate appearance."
        
        if stanza_family_names:
            family_names_list = list(stanza_family_names)  # Convert set to list
            if len(family_names_list) == 1:
                family_member_requirements = f"Include {family_names_list[0]} and use their photo as reference for accurate appearance."
            else:
                family_member_requirements = f"Include {', '.join(family_names_list[:-1])} and {family_names_list[-1]}, using their photos as reference for accurate appearance."
        
        # Collect only relevant reference images (baby photo + photos of characters in stanza)
        reference_images = []
        if baby_photo:
            reference_images.append(baby_photo)
        reference_images.extend(relevant_parent_photos)
        reference_images.extend(relevant_family_photos)
        
        # Load and format the prompt template
        prompt_template = load_prompt_template()
        prompt = prompt_template.format(
            baby_name=baby_name,
            baby_age=baby_age,
            baby_characteristics=baby_characteristics,
            stanza_number=stanza_number,
            total_stanzas=total_stanzas,
            stanza_text=stanza,
            parent_requirements=parent_requirements,
            family_member_requirements=family_member_requirements
        )
        
        logger.info(f"Generated prompt for stanza {stanza_number}: {prompt}")
        logger.info(f"Using {len(reference_images)} reference images for stanza {stanza_number}")
        
        # Generate the illustration
        image_data = await openai_service.generate_illustration(
            prompt=prompt,
            reference_images=reference_images
        )
        
        if not image_data:
            raise ValueError(f"Failed to generate illustration for stanza {stanza_number}")
            
        return image_data
        
    except Exception as e:
        logger.error(f"Error generating illustration for stanza {stanza_number}: {str(e)}")
        raise

@app.post("/generate-illustration", response_model=IllustrationResponse)
async def generate_illustration(
    request: IllustrationRequest,
    user_id: str = Depends(get_current_user)
) -> IllustrationResponse:
    """Generate illustrations for a poem.
    
    Args:
        request: The illustration request containing poem text, baby, parents, and family member information
        user_id: The ID of the authenticated user
    
    Returns:
        IllustrationResponse containing the generated images for each stanza
    """
    try:
        # Create storybook document
        storybook_id = await firebase_service.create_storybook(
            user_id=user_id,
            request_data=request.dict()
        )
        logger.info(f"Created storybook {storybook_id} for user {user_id} in Firestore database 'illustration-server'")
        
        # Split poem into stanzas
        stanzas = split_poem_into_stanzas(request.poem_text)
        total_stanzas = len(stanzas)
        logger.info(f"Processing {total_stanzas} stanzas in parallel")
        
        # Create tasks for parallel processing
        tasks = []
        for i, stanza in enumerate(stanzas):
            task = asyncio.create_task(
                generate_illustration_for_stanza(
                    stanza=stanza,
                    stanza_number=i+1,
                    request=request,
                    total_stanzas=total_stanzas
                )
            )
            tasks.append((i+1, task))
        
        # Process results as they complete
        image_data = {}
        errors = []
        
        for stanza_num, task in tasks:
            try:
                # Wait for each task with a timeout
                image = await asyncio.wait_for(task, timeout=300)  # 5 min timeout per illustration
                if image:
                    # Add illustration to storybook
                    await firebase_service.add_illustration(
                        storybook_id=storybook_id,
                        user_id=user_id,
                        stanza_number=stanza_num,
                        image_data=image,
                        prompt=f"Generated for stanza {stanza_num}"
                    )
                    # Store the Cloud Storage URL in the response
                    image_data[str(stanza_num)] = image
                    logger.info(f"Successfully added illustration for stanza {stanza_num} to storybook {storybook_id} in Firestore")
                else:
                    errors.append(f"Failed to generate illustration for stanza {stanza_num}")
            except asyncio.TimeoutError:
                errors.append(f"Timeout generating illustration for stanza {stanza_num}")
                logger.error(f"Timeout generating illustration for stanza {stanza_num}")
            except Exception as e:
                errors.append(f"Error generating illustration for stanza {stanza_num}: {str(e)}")
                logger.error(f"Error generating illustration for stanza {stanza_num}: {str(e)}")
        
        if not image_data:
            # Update storybook status to failed
            await firebase_service.update_storybook_status(
                storybook_id=storybook_id,
                status='failed'
            )
            logger.error(f"Failed to generate any illustrations for storybook {storybook_id}")
            raise ValueError("Failed to generate any illustrations")
        
        # Update storybook status to completed
        await firebase_service.update_storybook_status(
            storybook_id=storybook_id,
            status='completed'
        )
        logger.info(f"Updated storybook {storybook_id} status to completed")
        
        # Prepare response message
        if errors:
            message = f"Generated {len(image_data)} out of {total_stanzas} illustrations. Errors: {'; '.join(errors)}"
        else:
            message = f"Successfully generated all {len(image_data)} illustrations"
        
        logger.info(message)
        return IllustrationResponse(
            status="success",
            message=message,
            image_data=image_data
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return IllustrationResponse(
            status="error",
            message="Failed to generate illustrations",
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating illustrations: {str(e)}")
        return IllustrationResponse(
            status="error",
            message="Failed to generate illustrations",
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
