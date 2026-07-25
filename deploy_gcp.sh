#!/bin/bash
# Google Cloud Run Deployment Script for MindCare AI

echo "🚀 Deploying MindCare AI to Google Cloud Run..."

# Set project parameters
SERVICE_NAME="mindcare-ai"
REGION="us-central1"
PROJECT="salesforce-503116"

# Run Cloud Build and Deploy container to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT="$PROJECT",GCP_LOCATION="$REGION"

echo "✅ Deployment complete! Check the Cloud Run URL in the command output above."
