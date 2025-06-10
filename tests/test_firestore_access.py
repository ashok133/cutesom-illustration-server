"""Test Firestore access and all collections."""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.firebase_service import firebase_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_firestore_access():
    """Test basic Firestore access and all collections."""
    try:
        # Test user data
        test_user = {
            'uid': 'test-user-123',
            'email': 'test@example.com'
        }
        
        # 1. Test User Creation
        logger.info("Testing user creation...")
        user_id = await firebase_service.create_user(test_user)
        logger.info(f"Created test user with ID: {user_id}")
        
        # 2. Test Storybook Creation
        logger.info("\nTesting storybook creation...")
        test_request = {
            'poemText': 'Test poem',
            'baby': {
                'name': 'Test Baby',
                'age': '2 years',
                'photo': 'base64_placeholder'
            },
            'parents': {
                'parent1': {
                    'name': 'Test Parent 1',
                    'photo': 'base64_placeholder'
                },
                'parent2': {
                    'name': 'Test Parent 2',
                    'photo': 'base64_placeholder'
                }
            }
        }
        
        storybook_id = await firebase_service.create_storybook(user_id, test_request)
        logger.info(f"Created test storybook with ID: {storybook_id}")
        
        # 3. Test Storybook Status Update
        logger.info("\nTesting storybook status update...")
        await firebase_service.update_storybook_status(storybook_id, 'completed')
        logger.info("Updated storybook status to 'completed'")
        
        # 4. Test Adding Illustrations
        logger.info("\nTesting illustration addition...")
        test_illustrations = [
            {
                'stanza_number': 1,
                'image_url': 'https://example.com/image1.jpg',
                'prompt': 'Test prompt 1'
            },
            {
                'stanza_number': 2,
                'image_url': 'https://example.com/image2.jpg',
                'prompt': 'Test prompt 2'
            }
        ]
        
        for illustration in test_illustrations:
            await firebase_service.add_illustration(
                storybook_id,
                illustration['stanza_number'],
                illustration['image_url'],
                illustration['prompt']
            )
            logger.info(f"Added illustration for stanza {illustration['stanza_number']}")
        
        # 5. Test Getting Storybook
        logger.info("\nTesting storybook retrieval...")
        storybook = await firebase_service.get_storybook(storybook_id)
        logger.info(f"Retrieved storybook with {len(storybook.get('illustrations', []))} illustrations")
        
        # 6. Test Getting User's Storybooks
        logger.info("\nTesting user's storybooks retrieval...")
        storybooks = await firebase_service.get_user_storybooks(user_id)
        logger.info(f"User has {len(storybooks)} storybooks")
        
        # Print final storybook data for verification
        logger.info("\nFinal storybook data:")
        logger.info(f"Status: {storybook.get('status')}")
        logger.info(f"Number of illustrations: {len(storybook.get('illustrations', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Firestore access: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_firestore_access()) 