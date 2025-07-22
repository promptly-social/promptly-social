# Standalone Monitoring Deployment - Staging
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Data sources to get information about existing infrastructure
data "google_project" "current" {}

# Note: Data sources are commented out because monitoring should be deployable
# independently of infrastructure. The monitoring module uses resource naming
# conventions and doesn't require data sources to function properly.
# 
# If you need to reference specific infrastructure resources, you can:
# 1. Enable these data sources after infrastructure is deployed
# 2. Use terraform import to bring existing resources into state
# 3. Pass resource names/IDs via variables

# Uncomment these data sources only after infrastructure resources exist:
# 
# # Get Cloud Run service information
# data "google_cloud_run_service" "backend" {
#   count    = var.enable_cloud_run_monitoring ? 1 : 0
#   name     = "${var.app_name}-backend"
#   location = var.region
# }
# 
# # Get Cloud SQL instance information
# data "google_sql_database_instance" "main" {
#   count = var.enable_cloud_sql_monitoring ? 1 : 0
#   name  = "${var.app_name}-db-${var.environment}"
# }
# 
# # Get Cloud Functions information
# data "google_cloudfunctions_function" "user_activity" {
#   count  = var.enable_cloud_function_monitoring ? 1 : 0
#   name   = "${var.app_name}-user-activity-analysis-${var.environment}"
#   region = var.region
# }
# 
# data "google_cloudfunctions_function" "generate_suggestions" {
#   count  = var.enable_cloud_function_monitoring ? 1 : 0
#   name   = "${var.app_name}-generate-suggestions-${var.environment}"
#   region = var.region
# }
# 
# data "google_cloudfunctions_function" "post_scheduler" {
#   count  = var.enable_cloud_function_monitoring ? 1 : 0
#   name   = "${var.app_name}-unified-post-scheduler-${var.environment}"
#   region = var.region
# }
# 
# data "google_cloudfunctions_function" "analyze" {
#   count  = var.enable_cloud_function_monitoring ? 1 : 0
#   name   = "${var.app_name}-analyze-${var.environment}"
#   region = var.region
# }
# 
# # Get Load Balancer information
# data "google_compute_global_forwarding_rule" "backend_lb" {
#   count = var.enable_load_balancer_monitoring ? 1 : 0
#   name  = "${var.app_name}-backend-lb"
# }

# Monitoring Module - Now completely independent
module "monitoring" {
  source = "../../../modules/monitoring"
  
  # Required variables
  project_id  = var.project_id
  app_name    = var.app_name
  environment = var.environment
  
  # Notification configuration
  notification_emails = var.monitoring_notification_emails
  slack_webhook_url   = var.monitoring_slack_webhook_url
  
  # Feature toggles - can be controlled independently
  enable_cloud_function_monitoring  = var.enable_cloud_function_monitoring
  enable_cloud_run_monitoring      = var.enable_cloud_run_monitoring
  enable_cloud_sql_monitoring      = var.enable_cloud_sql_monitoring
  enable_cloud_scheduler_monitoring = var.enable_cloud_scheduler_monitoring
  enable_load_balancer_monitoring  = var.enable_load_balancer_monitoring
  enable_uptime_checks             = var.enable_uptime_checks
  enable_custom_metrics            = var.enable_custom_metrics
  enable_dashboards                = var.enable_monitoring_dashboards
  
  # Uptime check endpoints - configured independently
  api_endpoint      = var.api_endpoint
  frontend_endpoint = var.frontend_endpoint
  
  # Custom thresholds
  cloud_function_error_threshold              = var.monitoring_cloud_function_error_threshold
  cloud_function_execution_time_threshold_ms  = var.monitoring_cloud_function_execution_time_threshold_ms
  cloud_run_error_threshold                   = var.monitoring_cloud_run_error_threshold
  cloud_run_latency_threshold_ms              = var.monitoring_cloud_run_latency_threshold_ms
  cloud_sql_cpu_threshold                     = var.monitoring_cloud_sql_cpu_threshold
  cloud_sql_memory_threshold                  = var.monitoring_cloud_sql_memory_threshold
  cloud_sql_connections_threshold             = var.monitoring_cloud_sql_connections_threshold
  cloud_scheduler_failure_threshold           = var.monitoring_cloud_scheduler_failure_threshold
  load_balancer_error_threshold               = var.monitoring_load_balancer_error_threshold
}
