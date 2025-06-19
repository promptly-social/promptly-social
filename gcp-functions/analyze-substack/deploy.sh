#!/bin/bash

# GCP Cloud Function Deployment Script
# Usage: ./deploy.sh [project-id] [region]

set -e

# Configuration
PROJECT_ID=${1:-your-gcp-project-id}
REGION=${2:-us-central1}
FUNCTION_NAME="analyze-substack"
MEMORY="512MB"
TIMEOUT="540s"
RUNTIME="python311"

echo "🚀 Starting deployment of Cloud Function: $FUNCTION_NAME"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Runtime: $RUNTIME"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: No active gcloud authentication found. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
echo "🔧 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable logging.googleapis.com

# Deploy the function
echo "📦 Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=analyze_substack \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --trigger=http \
    --allow-unauthenticated \
    --set-env-vars="FUNCTION_TARGET=analyze_substack" \
    --max-instances=10

# Get the function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(serviceConfig.uri)")

echo "✅ Deployment completed successfully!"
echo "🔗 Function URL: $FUNCTION_URL"
echo ""
echo "📝 Next steps:"
echo "   1. Set environment variables in GCP Console:"
echo "      - SUPABASE_URL"
echo "      - SUPABASE_SERVICE_ROLE_KEY"
echo "   2. Update your backend service with this URL:"
echo "      GCP_ANALYSIS_FUNCTION_URL=$FUNCTION_URL"
echo ""
echo "🔧 To set environment variables from command line:"
echo "   gcloud functions deploy $FUNCTION_NAME \\"
echo "     --update-env-vars SUPABASE_URL=your_url,SUPABASE_SERVICE_ROLE_KEY=your_key \\"
echo "     --region=$REGION" 