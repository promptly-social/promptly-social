# Staging Environment Configuration
project_id = "promptly-social-staging"
region     = "us-central1"
zone       = "us-central1-a"

# Application Configuration
app_name    = "promptly"
environment = "staging"

# Docker Registry
docker_registry_location = "us-central1"

# Cloud Run Configuration - Staging optimized for cost
cloud_run_min_instances = 0  # Allow scale to zero for cost savings in staging
cloud_run_max_instances = 10
cloud_run_memory        = "1Gi"
cloud_run_cpu          = "1"

# Security & Backup
enable_deletion_protection = false  # Allow easier cleanup in staging

# CORS Configuration
cors_origins = [
  "https://staging.promptly.social"
]

# GitHub repository for Workload Identity Federation
github_repo = "promptly-social/promptly-social" 

# API Domain Name
api_domain_name = "api.staging.promptly.social"

# Frontend Domain Name
frontend_domain_name = "staging.promptly.social" 