#!/bin/bash

# Deployment script for Promptly Backend
# This script helps with local development and deployment tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=""
REGION="us-central1"
ENVIRONMENT="staging"
ACTION="deploy"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -p, --project-id PROJECT_ID     GCP project ID (required)"
    echo "  -r, --region REGION             GCP region (default: us-central1)"
    echo "  -e, --environment ENV           Environment: staging|production (default: staging)"
    echo "  -a, --action ACTION             Action: deploy|build|test|setup (default: deploy)"
    echo "  -h, --help                      Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 -p my-project -e staging -a setup"
    echo "  $0 -p my-project -e production -a deploy"
    echo "  $0 -p my-project -a test"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PROJECT_ID" ]]; then
    print_error "Project ID is required"
    show_usage
    exit 1
fi

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Environment must be 'staging' or 'production'"
    exit 1
fi

# Validate action
if [[ "$ACTION" != "deploy" && "$ACTION" != "build" && "$ACTION" != "test" && "$ACTION" != "setup" ]]; then
    print_error "Action must be 'deploy', 'build', 'test', or 'setup'"
    exit 1
fi

print_info "Starting $ACTION for $ENVIRONMENT environment"
print_info "Project ID: $PROJECT_ID"
print_info "Region: $REGION"

# Function to setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Authenticate with gcloud
    print_info "Authenticating with GCP..."
    gcloud auth login
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    print_info "Enabling required APIs..."
    gcloud services enable run.googleapis.com
    gcloud services enable sql-component.googleapis.com
    gcloud services enable sqladmin.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    
    print_success "Environment setup completed"
}

# Function to run tests
run_tests() {
    print_info "Running tests..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_info "Installing dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    # Run linting
    print_info "Running linting..."
    black --check .
    isort --check-only .
    flake8 .
    
    # Run tests
    print_info "Running tests..."
    pytest -v --cov=app --cov-report=term-missing
    
    print_success "Tests completed successfully"
}

# Function to build Docker image
build_image() {
    print_info "Building Docker image..."
    
    cd backend
    
    # Build image
    docker build -t promptly-backend:latest .
    
    # Test image
    print_info "Testing Docker image..."
    docker run --rm -d --name test-container -p 8001:8000 promptly-backend:latest
    sleep 10
    
    # Check if container is running
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        print_success "Docker image build and test successful"
    else
        print_error "Docker image test failed"
        docker logs test-container
        docker stop test-container
        exit 1
    fi
    
    docker stop test-container
}

# Function to deploy to GCP
deploy_to_gcp() {
    print_info "Deploying to GCP..."
    
    # Set variables
    SERVICE_NAME="promptly-backend-$ENVIRONMENT"
    REPO_NAME="promptly-backend"
    IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:latest"
    
    cd backend
    
    # Build and push image
    print_info "Building and pushing image to Artifact Registry..."
    gcloud builds submit --tag $IMAGE_NAME .
    
    # Deploy to Cloud Run
    print_info "Deploying to Cloud Run..."
    gcloud run deploy $SERVICE_NAME \
        --image=$IMAGE_NAME \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --port=8000 \
        --memory=2Gi \
        --cpu=2 \
        --min-instances=0 \
        --max-instances=100 \
        --set-env-vars="ENVIRONMENT=$ENVIRONMENT"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    print_success "Deployment completed successfully"
    print_success "Service URL: $SERVICE_URL"
}

# Execute action
case $ACTION in
    setup)
        setup_environment
        ;;
    test)
        run_tests
        ;;
    build)
        build_image
        ;;
    deploy)
        setup_environment
        run_tests
        build_image
        deploy_to_gcp
        ;;
esac

print_success "Script completed successfully!" 