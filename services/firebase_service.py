"""Firebase service for database operations."""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
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
                    # Check if running in Cloud Run
                    if os.getenv('K_SERVICE'):  # Cloud Run sets this environment variable
                        logger.info("Initializing Firebase in Cloud Run environment")
                        # Use default credentials in Cloud Run
                        cred = credentials.ApplicationDefault()
                        firebase_admin.initialize_app(cred, {
                            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                        })
                    else:
                        # Local development - use service account key
                        logger.info("Initializing Firebase in local development environment")
                        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                        if not cred_path:
                            raise ValueError(
                                "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. "
                                "Please set it to the path of your Firebase service account JSON file."
                            )
                        if not os.path.exists(cred_path):
                            raise ValueError(
                                f"Firebase service account file not found at: {cred_path}. "
                                "Please check if the path is correct."
                            )
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred, {
                            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                        })
                
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
            # Remove data URI prefix if present
            if image_data.startswith('data:image/jpeg;base64,'):
                image_data = image_data.replace('data:image/jpeg;base64,', '')
            
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
            output.seek(0)
            
            logger.info(f"Preprocessed image: {img.size} -> {new_size}, quality: {quality}")
            return output.read()
            
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
            str: The public URL of the stored image
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
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Get the public URL
            public_url = blob.public_url
            logger.info(f"Stored request image {image_type} to {public_url}")
            
            return public_url
            
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
            
            if 'parents' in request_data:
                if 'parent1' in request_data['parents'] and 'photo' in request_data['parents']['parent1']:
                    request_data['parents']['parent1']['photo'] = await self.store_request_image(
                        user_id=user_id,
                        storybook_id=storybook_id,
                        image_type='parent1',
                        image_data=request_data['parents']['parent1']['photo']
                    )
                
                if 'parent2' in request_data['parents'] and 'photo' in request_data['parents']['parent2']:
                    request_data['parents']['parent2']['photo'] = await self.store_request_image(
                        user_id=user_id,
                        storybook_id=storybook_id,
                        image_type='parent2',
                        image_data=request_data['parents']['parent2']['photo']
                    )
            
            if 'family_members' in request_data:
                for i, member in enumerate(request_data['family_members']):
                    if 'photo' in member:
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
            str: The public URL of the uploaded image
            
        TODO: Migrate to uniform bucket-level access and use Firebase Auth:
        1. Enable uniform bucket-level access
        2. Update storage rules to use Firebase Auth
        3. Store storage paths instead of URLs in Firestore
        4. Use Firebase Storage SDK on frontend to get authenticated URLs
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
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Get the public URL
            public_url = blob.public_url
            logger.info(f"Uploaded image to {public_url}")
            
            return public_url
            
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
            str: The public URL of the uploaded cover
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
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Get the public URL
            public_url = blob.public_url
            logger.info(f"Uploaded cover to {public_url}")
            
            return public_url
            
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
    
    async def get_user_storybooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all storybooks for a user."""
        try:
            # Get all storybooks and filter in memory
            storybooks_ref = self.db.collection('storybooks')
            storybooks = []
            
            for doc in storybooks_ref.stream():
                data = doc.to_dict()
                if data.get('userId') == user_id:
                    storybooks.append(data)
            
            return storybooks
            
        except Exception as e:
            logger.error(f"Error getting user storybooks: {str(e)}")
            raise

# Create singleton instance
firebase_service = FirebaseService() 