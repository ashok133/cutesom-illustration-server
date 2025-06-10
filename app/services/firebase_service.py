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
    
    async def create_storybook(self, user_id: str, request_data: Dict[str, Any]) -> str:
        """Create a new storybook document."""
        try:
            # Get user document
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                raise ValueError(f"User {user_id} not found")
            
            # Create storybook document
            storybook_ref = self.db.collection('storybooks').document()
            
            storybook_data = {
                'id': storybook_ref.id,
                'userId': user_id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'pending',
                'request': request_data,
                'illustrations': []
            }
            
            # Create storybook document
            storybook_ref.set(storybook_data)
            logger.info(f"Created new storybook: {storybook_ref.id}")
            return storybook_ref.id
            
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