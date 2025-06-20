# Production Environment Configuration
project_id = "promptly-social"
region     = "us-central1"
zone       = "us-central1-a"

# Application Configuration
app_name    = "promptly"
environment = "production"

# Docker Registry
docker_registry_location = "us-central1"

# Cloud Run Configuration - Production optimized for performance
cloud_run_min_instances = 1   # Always keep at least 1 instance running
cloud_run_max_instances = 100
cloud_run_memory        = "2Gi"
cloud_run_cpu          = "2"

# Security & Backup
enable_deletion_protection = true  # Protect production resources

# CORS Configuration
cors_origins = [
  "https://promptly.social",
  "https://www.promptly.social"
]

# GitHub repository for Workload Identity Federation
github_repo = "promptly-social/promptly-social"

# API Domain Name
api_domain_name = "api.promptly.social"

# Frontend Domain Name
frontend_domain_name = "promptly.social" 