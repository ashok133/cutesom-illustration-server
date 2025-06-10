"""Initialize Firestore database with schema."""
import os
import sys
import asyncio
import logging
from datetime import datetime, timezone

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.services.firebase_service import firebase_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_collections():
    """Create initial collections and indexes."""
    try:
        # Create a test user to verify users collection
        test_user = {
            'uid': 'test-user-123',
            'email': 'test@example.com',
            'displayName': 'Test User',
            'photoURL': 'https://example.com/photo.jpg',
            'createdAt': datetime.now(timezone.utc),
            'lastLoginAt': datetime.now(timezone.utc),
            'usage': {
                'totalStorybooks': 0,
                'totalIllustrations': 0,
                'lastStorybookAt': None,
                'subscriptionStatus': 'free'
            }
        }
        
        # Create test user
        user_id = await firebase_service.create_user(test_user)
        logger.info(f"Created test user with ID: {user_id}")
        
        # Create a test storybook to verify storybooks collection
        test_storybook = {
            'id': 'test-storybook-123',
            'userId': user_id,
            'userEmail': test_user['email'],
            'createdAt': datetime.now(timezone.utc),
            'updatedAt': datetime.now(timezone.utc),
            'status': 'completed',
            'request': {
                'poemText': 'Test poem',
                'baby': {
                    'name': 'Test Baby',
                    'age': '1 year',
                    'characteristics': 'Happy and playful'
                }
            },
            'illustrations': {
                '1': {
                    'imageUrl': 'https://example.com/test.jpg',
                    'storagePath': 'test/path.jpg',
                    'prompt': 'Test prompt',
                    'createdAt': datetime.now(timezone.utc),
                    'status': 'completed'
                }
            },
            'metrics': {
                'totalStanzas': 1,
                'completedStanzas': 1,
                'failedStanzas': 0,
                'totalGenerationTime': 10,
                'averageGenerationTime': 10
            },
            'cache': {
                'lastAccessed': datetime.now(timezone.utc),
                'accessCount': 1,
                'isCached': True
            }
        }
        
        # Create test storybook
        storybook_id = await firebase_service.create_storybook(user_id, test_storybook)
        logger.info(f"Created test storybook with ID: {storybook_id}")
        
        # Create initial analytics document
        analytics_ref = firebase_service.db.collection('analytics').document('daily')
        analytics_ref.set({
            'id': 'daily',
            'date': datetime.now(timezone.utc),
            'metrics': {
                'totalRequests': 0,
                'successfulRequests': 0,
                'failedRequests': 0,
                'averageGenerationTime': 0,
                'totalGenerationTime': 0,
                'totalStanzas': 0,
                'totalIllustrations': 0
            },
            'errors': {}
        })
        logger.info("Created initial analytics document")
        
        # Verify collections
        collections = ['users', 'storybooks', 'analytics']
        for collection in collections:
            docs = firebase_service.db.collection(collection).limit(1).get()
            if docs:
                logger.info(f"Verified {collection} collection exists and is accessible")
            else:
                logger.warning(f"Collection {collection} exists but is empty")
        
        logger.info("Firestore initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing Firestore: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(create_collections()) 