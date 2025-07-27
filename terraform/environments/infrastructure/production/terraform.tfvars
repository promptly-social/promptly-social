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

manage_cloud_run_service = true
manage_frontend_infra = true

terraform_service_account_email = "promptly-tf-sa-production@promptly-social.iam.gserviceaccount.com"

# Cloud SQL Configuration - Production (high-availability)
cloud_sql_tier                    = "db-custom-1-3840"
cloud_sql_disk_size              = 100
cloud_sql_disk_autoresize_limit  = 500
cloud_sql_availability_type      = "REGIONAL"
cloud_sql_deletion_protection    = true   # Strong protection for production
cloud_sql_backup_retention_count = 30     # Longer retention for production
cloud_sql_authorized_networks    = []     # Use private IP only

# Cloud Function service accounts that need database access
# All Cloud Functions use the same App Service Account
cloud_function_sa_emails = [
  "promptly-app-sa-production@promptly-social.iam.gserviceaccount.com"
]

# Monitoring Configuration - Production
# Email notifications for production alerts
monitoring_notification_emails = [
  "ops-team@promptly.social",
  "production-alerts@promptly.social",
  "engineering@promptly.social"
]

# Slack webhook for production alerts (recommended for immediate notifications)
# monitoring_slack_webhook_url = "https://hooks.slack.com/services/YOUR/PRODUCTION/WEBHOOK"

# Service management flags (enable monitoring for deployed services)
manage_cloud_functions = true
manage_cloud_sql = true
manage_cloud_scheduler = true
manage_frontend_deployment = true

# Monitoring feature toggles - Production (all enabled)
enable_uptime_checks = true
enable_custom_metrics = true
enable_monitoring_dashboards = true

# Monitoring thresholds - Production (strict thresholds for production)
monitoring_cloud_function_error_threshold = 0.05  # Very low error tolerance
monitoring_cloud_function_execution_time_threshold_ms = 300000  # 5 minutes
monitoring_cloud_run_error_threshold = 0.5  # Low error tolerance
monitoring_cloud_run_latency_threshold_ms = 3000  # 3 seconds
monitoring_cloud_sql_cpu_threshold = 0.7  # 70% CPU before alerting
monitoring_cloud_sql_memory_threshold = 0.8  # 80% memory before alerting
monitoring_cloud_sql_connections_threshold = 200  # Higher connection limit for production
monitoring_cloud_scheduler_failure_threshold = 1  # Alert on first failure in production
monitoring_load_balancer_error_threshold = 2.0  # Low error tolerance for production