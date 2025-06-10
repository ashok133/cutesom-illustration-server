#!/bin/bash

# Set your project ID
export PROJECT_ID="cutesom"

# Create indexes for storybooks collection
gcloud firestore indexes composite create \
    --collection-group=storybooks \
    --query-scope=COLLECTION \
    --field-config field-path=userId,order=ASCENDING \
    --field-config field-path=createdAt,order=DESCENDING

gcloud firestore indexes composite create \
    --collection-group=storybooks \
    --query-scope=COLLECTION \
    --field-config field-path=status,order=ASCENDING \
    --field-config field-path=createdAt,order=DESCENDING

gcloud firestore indexes composite create \
    --collection-group=storybooks \
    --query-scope=COLLECTION \
    --field-config field-path=cache.isCached,order=ASCENDING \
    --field-config field-path=cache.lastAccessed,order=DESCENDING

# Create indexes for users collection
gcloud firestore indexes composite create \
    --collection-group=users \
    --query-scope=COLLECTION \
    --field-config field-path=email,order=ASCENDING

gcloud firestore indexes composite create \
    --collection-group=users \
    --query-scope=COLLECTION \
    --field-config field-path=createdAt,order=DESCENDING

# Create indexes for analytics collection
gcloud firestore indexes composite create \
    --collection-group=analytics \
    --query-scope=COLLECTION \
    --field-config field-path=date,order=DESCENDING

echo "Indexes created successfully!" 