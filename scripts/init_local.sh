#!/bin/bash

# Check if service account key path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-service-account-key.json>"
    echo "Example: $0 ./cutesom-server-key.json"
    exit 1
fi

# Check if service account key file exists
if [ ! -f "$1" ]; then
    echo "Error: Service account key file not found at $1"
    exit 1
fi

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="$1"
export FIREBASE_STORAGE_BUCKET="cutesom-5eea4.firebasestorage.app"

# Run the initialization script
echo "Running Firestore initialization..."
python scripts/init_firestore.py

# Check if initialization was successful
if [ $? -eq 0 ]; then
    echo "Firestore initialization completed successfully!"
else
    echo "Firestore initialization failed. Please check the logs above for errors."
fi 