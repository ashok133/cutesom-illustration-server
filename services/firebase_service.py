"""Firebase service for database operations."""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore import Client
from google.cloud.firestore_v1.client import Client as FirestoreClient
import base64
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseService:
    """Firebase service for database operations."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase service."""
        if not self._initialized:
            try:
                # Initialize Firebase Admin SDK
                if not firebase_admin._apps:
                    # Use Application Default Credentials (ADC) for both Cloud Run and Local
                    # local: looks for GOOGLE_APPLICATION_CREDENTIALS
                    # cloud: looks for metadata server
                    logger.info("Initializing Firebase with Application Default Credentials")
                    
                    try:
                        cred = credentials.ApplicationDefault()
                        firebase_admin.initialize_app(cred, {
                            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                        })
                    except Exception as e:
                        logger.error(f"Failed to initialize Firebase credentials: {e}")
                        logger.error("Ensure GOOGLE_APPLICATION_CREDENTIALS is set locally or you are in a valid Cloud environment.")
                        raise
                
                # Initialize Firestore client
                self.db: Client = FirestoreClient(
                    project='cutesom',
                    database='illustration-server'
                )
                self.bucket = storage.bucket()
                
                logger.info("Firebase service initialized successfully")
                self._initialized = True
                
            except Exception as e:
                logger.error(f"Error initializing Firebase service: {str(e)}")
                raise
    
    def generate_signed_url(self, blob_path: str, expiration_minutes: int = 60) -> Optional[str]:
        """Generate a signed URL for a storage blob.

        Args:
            blob_path: Path to the blob in storage
            expiration_minutes: URL expiration time in minutes

        Returns:
            str: Signed URL or None if blob_path is invalid/empty
        """
        if not blob_path:
            return None

        try:
            # Check if it's already a public URL (legacy support)
            if blob_path.startswith('http'):
                return blob_path

            blob = self.bucket.blob(blob_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
            return url
        except Exception as e:
            logger.error(f"Error generating signed URL for {blob_path}: {str(e)}")
            return None

    def _preprocess_image(self, image_data: str, max_size: int = 1024, quality: int = 85) -> bytes:
        """Preprocess image to reduce size while maintaining quality.
        
        Args:
            image_data: Base64 encoded image data with data URI prefix
            max_size: Maximum dimension (width or height) in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            bytes: Processed image data
        """
        try:
            # Clean up the base64 string
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            # Remove any whitespace
            image_data = image_data.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Add padding if needed
            missing_padding = len(image_data) % 4
            if missing_padding:
                image_data += '=' * (4 - missing_padding)
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)
            
            # Open image from bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new dimensions while maintaining aspect ratio
            ratio = min(max_size / max(img.size), 1.0)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            
            # Resize image if needed
            if ratio < 1.0:
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to bytes with compression
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            result = output.getvalue()
            logger.info(f"Preprocessed image size: {len(result)} bytes")
            
            logger.info(f"Preprocessed image: {img.size} -> {new_size}, quality: {quality}")
            return result
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            # Return original image if preprocessing fails
            return image_data
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user document."""
        try:
            user_ref = self.db.collection('users').document(user_data['uid'])
            
            # Check if user already exists
            if user_ref.get().exists:
                # Update last login
                user_ref.update({
                    'lastLoginAt': firestore.SERVER_TIMESTAMP
                })
                return user_data['uid']
            
            # Create new user document
            user_ref.set({
                'uid': user_data['uid'],
                'email': user_data['email'],
                'createdAt': firestore.SERVER_TIMESTAMP,
                'lastLoginAt': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Created new user: {user_data['email']}")
            return user_data['uid']
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def store_request_image(
        self,
        user_id: str,
        storybook_id: str,
        image_type: str,
        image_data: str
    ) -> str:
        """Store a request image in Cloud Storage.
        
        Args:
            user_id: The user's ID
            storybook_id: The storybook's ID
            image_type: Type of image (e.g., 'baby', 'parent1', 'parent2', 'family_member')
            image_data: Base64 encoded image data with data URI prefix
            
        Returns:
            str: The storage path of the stored image
        """
        try:
            # Preprocess image
            processed_image_bytes = self._preprocess_image(image_data)
            
            # Create storage path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            storage_path = f"storybooks/{user_id}/{storybook_id}/request_images/{image_type}_{timestamp}.jpg"
            
            # Create blob and upload
            blob = self.bucket.blob(storage_path)
            blob.upload_from_string(
                processed_image_bytes,
                content_type='image/jpeg'
            )
            
            # Return the storage path instead of public URL
            logger.info(f"Stored request image {image_type} to {storage_path}")
            
            return storage_path
            
        except Exception as e:
            logger.error(f"Error storing request image: {str(e)}")
            raise

    async def create_storybook(self, user_id: str, request_data: Dict[str, Any]) -> str:
        """Create a new storybook document and store request images.
        
        Args:
            user_id: The user's ID
            request_data: The storybook request data
            
        Returns:
            str: The ID of the created storybook
        """
        try:
            # Get user document
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                raise ValueError(f"User {user_id} not found")
            
            # Create storybook document first to get the ID
            storybook_ref = self.db.collection('storybooks').document()
            storybook_id = storybook_ref.id
            
            # Store request images and update URLs
            if 'baby' in request_data and 'photo' in request_data['baby']:
                request_data['baby']['photo'] = await self.store_request_image(
                    user_id=user_id,
                    storybook_id=storybook_id,
                    image_type='baby',
                    image_data=request_data['baby']['photo']
                )
            
            # Process parents
            parents = request_data.get('parents')
            if parents:
                parent1 = parents.get('parent1')
                if parent1 and parent1.get('photo'):
                    parent1['photo'] = await self.store_request_image(
                        user_id=user_id,
                        storybook_id=storybook_id,
                        image_type='parent1',
                        image_data=parent1['photo']
                    )
                
                parent2 = parents.get('parent2')
                if parent2 and parent2.get('photo'):
                    parent2['photo'] = await self.store_request_image(
                        user_id=user_id,
                        storybook_id=storybook_id,
                        image_type='parent2',
                        image_data=parent2['photo']
                    )
            
            # Process family members
            family_members = request_data.get('family_members')
            if family_members:
                for i, member in enumerate(family_members):
                    if member.get('photo'):
                        member['photo'] = await self.store_request_image(
                            user_id=user_id,
                            storybook_id=storybook_id,
                            image_type=f'family_member_{i+1}',
                            image_data=member['photo']
                        )
            
            # Create storybook document with updated image URLs
            storybook_data = {
                'id': storybook_id,
                'userId': user_id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'pending',
                'request': request_data,
                'illustrations': []
            }
            
            # Create storybook document
            storybook_ref.set(storybook_data)
            logger.info(f"Created new storybook: {storybook_id}")
            return storybook_id
            
        except Exception as e:
            logger.error(f"Error creating storybook: {str(e)}")
            raise
    
    async def update_storybook_status(
        self,
        storybook_id: str,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Update storybook status."""
        try:
            storybook_ref = self.db.collection('storybooks').document(storybook_id)
            
            update_data = {
                'status': status
            }
            
            if error:
                update_data['error'] = error
            
            storybook_ref.update(update_data)
            logger.info(f"Updated storybook {storybook_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Error updating storybook status: {str(e)}")
            raise
    
    async def upload_image_to_storage(
        self,
        user_id: str,
        storybook_id: str,
        stanza_number: int,
        image_data: str
    ) -> str:
        """Upload an image to Cloud Storage.
        
        Args:
            user_id: The user's ID
            storybook_id: The storybook's ID
            stanza_number: The stanza number
            image_data: Base64 encoded image data with data URI prefix
            
        Returns:
            str: The storage path of the uploaded image
        """
        try:
            # Remove data URI prefix if present
            if image_data.startswith('data:image/jpeg;base64,'):
                image_data = image_data.replace('data:image/jpeg;base64,', '')
            
            # Decode base64 data
            image_bytes = base64.b64decode(image_data)
            
            # Create storage path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            storage_path = f"storybooks/{user_id}/illustrations/{stanza_number}_{timestamp}.jpg"
            
            # Create blob and upload
            blob = self.bucket.blob(storage_path)
            blob.upload_from_string(
                image_bytes,
                content_type='image/jpeg'
            )
            
            # Return the storage path
            logger.info(f"Uploaded image to {storage_path}")
            
            return storage_path
            
        except Exception as e:
            logger.error(f"Error uploading image to storage: {str(e)}")
            raise

    async def upload_cover_to_storage(
        self,
        user_id: str,
        storybook_id: str,
        cover_data: str
    ) -> str:
        """Upload a storybook cover to Cloud Storage.
        
        Args:
            user_id: The user's ID
            storybook_id: The storybook's ID
            cover_data: Base64 encoded image data with data URI prefix
            
        Returns:
            str: The storage path of the uploaded cover
        """
        try:
            # Remove data URI prefix if present
            if cover_data.startswith('data:image/jpeg;base64,'):
                cover_data = cover_data.replace('data:image/jpeg;base64,', '')
            
            # Decode base64 data
            image_bytes = base64.b64decode(cover_data)
            
            # Create storage path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            storage_path = f"storybooks/{user_id}/covers/{storybook_id}_{timestamp}.jpg"
            
            # Create blob and upload
            blob = self.bucket.blob(storage_path)
            blob.upload_from_string(
                image_bytes,
                content_type='image/jpeg'
            )
            
            # Return the storage path
            logger.info(f"Uploaded cover to {storage_path}")
            
            return storage_path
            
        except Exception as e:
            logger.error(f"Error uploading cover to storage: {str(e)}")
            raise

    async def add_illustration(
        self,
        storybook_id: str,
        user_id: str,
        stanza_number: int,
        image_data: str,
        prompt: str
    ) -> None:
        """Add an illustration to a storybook.
        
        Args:
            storybook_id: The storybook's ID
            user_id: The user's ID
            stanza_number: The stanza number
            image_data: Base64 encoded image data
            prompt: The prompt used to generate the image
        """
        try:
            # Upload image to Cloud Storage
            image_url = await self.upload_image_to_storage(
                user_id=user_id,
                storybook_id=storybook_id,
                stanza_number=stanza_number,
                image_data=image_data
            )
            
            storybook_ref = self.db.collection('storybooks').document(storybook_id)
            
            # Get current document
            doc = storybook_ref.get()
            if not doc.exists:
                raise ValueError(f"Storybook {storybook_id} not found")
            
            # Get current illustrations array
            current_data = doc.to_dict()
            illustrations = current_data.get('illustrations', [])
            
            # Add new illustration
            illustrations.append({
                'stanzaNumber': stanza_number,
                'imageUrl': image_url,
                'prompt': prompt,
                'createdAt': datetime.now()
            })
            
            # Update the entire illustrations array
            storybook_ref.update({
                'illustrations': illustrations
            })
            
            logger.info(f"Added illustration for stanza {stanza_number} to storybook {storybook_id}")
            
        except Exception as e:
            logger.error(f"Error adding illustration: {str(e)}")
            raise

    async def add_cover_to_storybook(
        self,
        storybook_id: str,
        cover_url: str
    ) -> None:
        """Add a cover URL to a storybook.
        
        Args:
            storybook_id: The storybook's ID
            cover_url: The URL of the cover image
        """
        try:
            storybook_ref = self.db.collection('storybooks').document(storybook_id)
            
            # Update the storybook with cover URL
            storybook_ref.update({
                'coverUrl': cover_url,
                'coverCreatedAt': datetime.now()
            })
            
            logger.info(f"Added cover to storybook {storybook_id}")
            
        except Exception as e:
            logger.error(f"Error adding cover to storybook: {str(e)}")
            raise

    async def get_storybook(self, storybook_id: str) -> Dict[str, Any]:
        """Get a storybook document."""
        try:
            storybook_ref = self.db.collection('storybooks').document(storybook_id)
            storybook_doc = storybook_ref.get()
            
            if not storybook_doc.exists:
                raise ValueError(f"Storybook {storybook_id} not found")
            
            return storybook_doc.to_dict()
            
        except Exception as e:
            logger.error(f"Error getting storybook: {str(e)}")
            raise

    async def get_storybook_details(self, storybook_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed storybook information with signed URLs.

        Args:
            storybook_id: The storybook ID
            user_id: The user ID (for verification)

        Returns:
            Dict containing storybook details with signed URLs
        """
        try:
            data = await self.get_storybook(storybook_id)

            # Verify user ownership
            if data.get('userId') != user_id:
                raise ValueError("Unauthorized access to storybook")

            # Generate signed URL for cover
            if data.get('coverUrl'):
                data['coverUrl'] = self.generate_signed_url(data['coverUrl'])

            # Generate signed URLs for illustrations
            if data.get('illustrations'):
                for illustration in data['illustrations']:
                    if illustration.get('imageUrl'):
                        illustration['imageUrl'] = self.generate_signed_url(illustration['imageUrl'])

            # Generate signed URLs for request images (baby photo, parents, etc.)
            request = data.get('request', {})

            if request.get('baby', {}).get('photo'):
                request['baby']['photo'] = self.generate_signed_url(request['baby']['photo'])

            if request.get('parents'):
                if request['parents'].get('parent1', {}).get('photo'):
                    request['parents']['parent1']['photo'] = self.generate_signed_url(request['parents']['parent1']['photo'])
                if request['parents'].get('parent2', {}).get('photo'):
                    request['parents']['parent2']['photo'] = self.generate_signed_url(request['parents']['parent2']['photo'])

            if request.get('family_members'):
                for member in request['family_members']:
                    if member.get('photo'):
                        member['photo'] = self.generate_signed_url(member['photo'])

            return data

        except Exception as e:
            logger.error(f"Error getting storybook details: {str(e)}")
            raise
    
    async def get_user_storybooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all storybooks for a user."""
        try:
            # Query Firestore filtering by userId
            storybooks_ref = self.db.collection('storybooks')
            query = storybooks_ref.where('userId', '==', user_id).order_by('createdAt', direction=firestore.Query.DESCENDING)
            
            storybooks = []
            for doc in query.stream():
                data = doc.to_dict()

                # Ensure ID is included
                if 'id' not in data:
                    data['id'] = doc.id

                # Generate signed URL for cover if it exists
                if data.get('coverUrl'):
                    data['coverUrl'] = self.generate_signed_url(data['coverUrl'])

                # We don't need to generate signed URLs for illustrations here as this is a summary

                storybooks.append(data)
            
            return storybooks
            
        except Exception as e:
            logger.error(f"Error getting user storybooks: {str(e)}")
            raise

# Create singleton instance
firebase_service = FirebaseService() 