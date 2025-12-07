#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="cutesom"
REGION="us-central1"
SERVICE_NAME="cutesom-illustration-server"
SERVICE_ACCOUNT="cutesom-server@${PROJECT_ID}.iam.gserviceaccount.com"
REPOSITORY="cutesom-illustration-server-repo"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}"
# FIREBASE_STORAGE_BUCKET="gs://cutesom-5eea4.firebasestorage.app"
FIREBASE_STORAGE_BUCKET="cutesom-storybooks"

# Setup credentials
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build the Docker image
echo "Building Docker image..."
docker build --platform=linux/amd64 -t ${IMAGE_NAME} .

# Push the image to Artifact Registry
echo "Pushing image to Artifact Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --project ${PROJECT_ID} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --timeout 3600 \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 1 \
  --memory 2Gi \
  --set-env-vars="PROJECT_ID=${PROJECT_ID}" \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET}" \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"

echo "✅ Deployment complete!"
echo "🌐 Service URL: $(gcloud run services describe ${SERVICE_NAME} --project ${PROJECT_ID} --platform managed --region ${REGION} --format 'value(status.url)')"