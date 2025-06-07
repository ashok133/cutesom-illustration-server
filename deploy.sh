#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="cutesom"
SERVICE_NAME="cutesom-illustration-server"
REGION="us-central1"
REPOSITORY="cutesom-illustration-server-repo"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}"

# Build the Docker image
echo "Building Docker image..."
docker build --platform=linux/amd64 -t ${IMAGE_NAME} .

# Push the image to Artifact Registry
echo "Pushing image to Artifact Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8080

echo "Deployment completed successfully!" 