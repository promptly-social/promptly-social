terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Generate source hash for versioning
locals {
  source_hash = substr(sha256(join("", concat([
    for f in fileset("${path.module}/../../../src/gcp-functions/user_activity_analysis", "**") :
    filesha256("${path.module}/../../../src/gcp-functions/user_activity_analysis/${f}")
  ], [
    for f in fileset("${path.module}/../../../src/gcp-functions/shared", "**") :
    filesha256("${path.module}/../../../src/gcp-functions/shared/${f}")
  ], [
    filesha256("${path.module}/../../../src/gcp-functions/main.py")
  ]))), 0, 8)
}

module "user_activity_analysis_function" {
  source = "../../../modules/user_activity_analysis_function"
  
  # Required variables for standardized pattern
  service_account_email = "${var.app_name}-app-sa-${var.environment}@${var.project_id}.iam.gserviceaccount.com"
  source_bucket         = "${var.app_name}-cf-source-${var.environment}"
  source_hash           = local.source_hash
  
  # Basic configuration
  project_id          = var.project_id
  region              = var.region
  app_name            = var.app_name
  environment         = var.environment
  function_name       = "user-activity-analysis-function-${var.environment}"
  function_source_dir = "../../../src/gcp-functions"
  
  # Scheduler configuration - once daily at midnight PDT
  schedule              = var.schedule
  timezone              = var.timezone
  scheduler_job_name    = "user-activity-analysis-trigger-${var.environment}"
  scheduler_paused      = var.scheduler_paused
  
  # Analysis configuration
  openrouter_model_primary     = var.openrouter_model_primary
  openrouter_models_fallback   = var.openrouter_models_fallback
  openrouter_model_temperature = var.openrouter_model_temperature
  post_threshold               = var.post_threshold
  message_threshold            = var.message_threshold
  max_retry_attempts           = var.max_retry_attempts
  analysis_timeout_minutes     = var.analysis_timeout_minutes
  batch_size                   = var.batch_size
  
  # Monitoring configuration
  enable_monitoring_alerts    = var.enable_monitoring_alerts
  enable_custom_metrics       = var.enable_custom_metrics
  enable_monitoring_dashboard = var.enable_monitoring_dashboard
  enable_scheduler_monitoring = var.enable_scheduler_monitoring
  notification_channels       = var.notification_channels
  
  # Alert thresholds
  error_rate_threshold         = var.error_rate_threshold
  execution_time_threshold_ms  = var.execution_time_threshold_ms
  scheduler_failure_threshold  = var.scheduler_failure_threshold
}

output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = module.user_activity_analysis_function.function_uri
}

output "function_name" {
  description = "The name of the deployed Cloud Function."
  value       = module.user_activity_analysis_function.function_name
}

output "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job."
  value       = module.user_activity_analysis_function.scheduler_job_name
}
