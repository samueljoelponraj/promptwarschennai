# Google Cloud Run PowerShell Deployment Script for MindCare AI

Write-Host "🚀 Deploying MindCare AI to Google Cloud Run..." -ForegroundColor Cyan

$SERVICE_NAME = "mindcare-ai"
$REGION = "us-central1"
$PROJECT = "salesforce-503116"

$ENV_STR = "GCP_PROJECT=$PROJECT,GCP_LOCATION=$REGION"

gcloud run deploy $SERVICE_NAME `
  --source . `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars $ENV_STR

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
