# Staging Environment Configuration
project_id = "promptly-social-staging"
region     = "us-central1"
zone       = "us-central1-a"
production_project_id = "promptly-social"

# Application Configuration
app_name    = "promptly"
environment = "staging" 

# Docker Registry
docker_registry_location = "us-central1"

# Terraform State Configuration
terraform_state_reader_service_accounts = []

# Cloud Run Configuration - Staging optimized for cost
manage_cloud_run_service = true
manage_backend_load_balancer = true
cloud_run_min_instances = 1
cloud_run_max_instances = 2
cloud_run_memory        = "1Gi"
cloud_run_cpu          = "1000m"

# Security & Backup
enable_deletion_protection = false  # Allow easier cleanup in staging

# DNS Configuration
manage_dns_zone = false  # Use shared production DNS zone

# CORS Configuration
cors_origins = [
  "https://staging.promptly.social"
]

# GitHub repository for Workload Identity Federation
github_repo = "promptly-social/promptly-social" 

# API Domain Name
api_domain_name = "api.staging.promptly.social"

# Frontend Configuration
manage_frontend_infra = true
frontend_domain_name  = "staging.promptly.social"

# Cloud SQL Configuration - Staging (cost-optimized)
cloud_sql_tier                    = "db-f1-micro"
cloud_sql_disk_size              = 20
cloud_sql_disk_autoresize_limit  = 50
cloud_sql_availability_type      = "ZONAL"
cloud_sql_deletion_protection    = false  # Allow easier cleanup in staging
cloud_sql_backup_retention_count = 3      # Shorter retention for staging
cloud_sql_transaction_log_retention_days = 3  # Match backup retention
cloud_sql_authorized_networks    = []     # Use private IP only

# Cloud Function service accounts that need database access
# All Cloud Functions use the same App Service Account
cloud_function_sa_emails = [
  "promptly-app-sa-staging@promptly-social-staging.iam.gserviceaccount.com"
] 

terraform_service_account_email = "promptly-tf-sa-staging@promptly-social-staging.iam.gserviceaccount.com"