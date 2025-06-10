"""Script to create Firestore index."""
import os
import sys
import logging
from google.cloud import firestore_admin_v1
from google.cloud.firestore_admin_v1 import types

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_index():
    """Create the required Firestore index."""
    try:
        # Initialize Firestore Admin client
        client = firestore_admin_v1.FirestoreAdminClient()
        
        # Project and database details
        project_id = "cutesom"
        database_id = "illustration-server"
        parent = f"projects/{project_id}/databases/{database_id}/collectionGroups/storybooks"
        
        # Define the index
        index = types.Index(
            query_scope=types.Index.QueryScope.COLLECTION,
            fields=[
                types.IndexField(
                    field_path="userId",
                    order=types.IndexField.Order.ASCENDING
                ),
                types.IndexField(
                    field_path="createdAt",
                    order=types.IndexField.Order.DESCENDING
                )
            ]
        )
        
        # Create the index
        operation = client.create_index(
            request={
                "parent": parent,
                "index": index
            }
        )
        
        # Wait for the operation to complete
        result = operation.result()
        logger.info(f"Created index: {result.name}")
        
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

if __name__ == "__main__":
    create_index() 