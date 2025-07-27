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
cloud_run_min_instances = 0  # Allow cold starts in staging to save cost
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

# Monitoring Configuration - Staging
# Email notifications for staging alerts
monitoring_notification_emails = [
  "dev-team@promptly.social",
  "staging-alerts@promptly.social"
]

# Optional Slack webhook for staging alerts
# monitoring_slack_webhook_url = "https://hooks.slack.com/services/YOUR/STAGING/WEBHOOK"

# Service management flags (enable monitoring for deployed services)
manage_cloud_functions = true
manage_cloud_sql = true
manage_cloud_scheduler = true
manage_frontend_deployment = true

# Monitoring feature toggles - Staging
enable_uptime_checks = true
enable_custom_metrics = true
enable_monitoring_dashboards = true

# Monitoring thresholds - Staging (more relaxed than production)
monitoring_cloud_function_error_threshold = 0.2  # Allow higher error rate in staging
monitoring_cloud_function_execution_time_threshold_ms = 900000  # 15 minutes
monitoring_cloud_run_error_threshold = 2.0  # Higher tolerance for staging
monitoring_cloud_run_latency_threshold_ms = 10000  # 10 seconds
monitoring_cloud_sql_cpu_threshold = 0.9  # 90% CPU before alerting
monitoring_cloud_sql_memory_threshold = 0.95  # 95% memory before alerting
monitoring_cloud_sql_connections_threshold = 50  # Lower connection limit for staging
monitoring_cloud_scheduler_failure_threshold = 3  # Allow more failures in staging
monitoring_load_balancer_error_threshold = 10.0  # Higher error tolerance