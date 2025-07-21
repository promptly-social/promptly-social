# Test configuration for scheduler functionality
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Test scheduler with different configurations
module "scheduler_test_hourly" {
  source = "../"

  project_id            = "test-project"
  region               = "us-central1"
  service_account_email = "test-sa@test-project.iam.gserviceaccount.com"
  source_bucket        = "test-source-bucket"
  source_hash          = "test-hash"
  function_source_dir  = "/tmp/test-source"
  
  # Hourly schedule test
  function_name       = "user-activity-analysis-hourly"
  scheduler_job_name  = "user-activity-analysis-hourly-trigger"
  schedule           = "0 * * * *"  # Every hour
  timezone           = "UTC"
  scheduler_paused   = false
  
  # Enhanced retry configuration
  scheduler_retry_count          = 5
  scheduler_max_retry_duration   = "3600s"  # 1 hour
  scheduler_min_backoff_duration = "10s"
  scheduler_max_backoff_duration = "600s"   # 10 minutes
  scheduler_max_doublings        = 6
  
  enable_scheduler_monitoring = true
}

module "scheduler_test_custom" {
  source = "../"

  project_id            = "test-project"
  region               = "us-central1"
  service_account_email = "test-sa@test-project.iam.gserviceaccount.com"
  source_bucket        = "test-source-bucket"
  source_hash          = "test-hash-2"
  function_source_dir  = "/tmp/test-source"
  
  # Custom schedule test (every 2 hours)
  function_name       = "user-activity-analysis-custom"
  scheduler_job_name  = "user-activity-analysis-custom-trigger"
  schedule           = "0 */2 * * *"  # Every 2 hours
  timezone           = "America/New_York"
  scheduler_paused   = true  # Start paused for testing
  
  # Minimal retry configuration
  scheduler_retry_count          = 2
  scheduler_max_retry_duration   = "900s"   # 15 minutes
  scheduler_min_backoff_duration = "5s"
  scheduler_max_backoff_duration = "120s"   # 2 minutes
  scheduler_max_doublings        = 3
  
  enable_scheduler_monitoring = false
}

# Test outputs
output "hourly_scheduler_job_name" {
  description = "Hourly test scheduler job name"
  value       = module.scheduler_test_hourly.scheduler_job_name
}

output "hourly_monitoring_topic" {
  description = "Hourly test monitoring topic"
  value       = module.scheduler_test_hourly.scheduler_monitoring_topic
}

output "custom_scheduler_job_name" {
  description = "Custom test scheduler job name"
  value       = module.scheduler_test_custom.scheduler_job_name
}

output "custom_monitoring_topic" {
  description = "Custom test monitoring topic (should be null)"
  value       = module.scheduler_test_custom.scheduler_monitoring_topic
}