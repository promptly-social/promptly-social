# Test configuration for monitoring and alerting functionality
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Test monitoring with full configuration
module "monitoring_test_full" {
  source = "../"

  project_id            = "test-project"
  region               = "us-central1"
  service_account_email = "test-sa@test-project.iam.gserviceaccount.com"
  source_bucket        = "test-source-bucket"
  source_hash          = "test-hash"
  function_source_dir  = "/tmp/test-source"
  
  function_name       = "user-activity-analysis-monitored"
  scheduler_job_name  = "user-activity-analysis-monitored-trigger"
  
  # Enable all monitoring features
  enable_scheduler_monitoring  = true
  enable_monitoring_alerts    = true
  enable_custom_metrics       = true
  enable_monitoring_dashboard = true
  
  # Custom thresholds for testing
  error_rate_threshold         = 0.05  # 0.05 errors/sec
  execution_time_threshold_ms  = 300000  # 5 minutes
  scheduler_failure_threshold  = 1
  
  # Mock notification channels
  notification_channels = [
    "projects/test-project/notificationChannels/test-channel-1",
    "projects/test-project/notificationChannels/test-channel-2"
  ]
}

# Test monitoring with minimal configuration
module "monitoring_test_minimal" {
  source = "../"

  project_id            = "test-project"
  region               = "us-central1"
  service_account_email = "test-sa@test-project.iam.gserviceaccount.com"
  source_bucket        = "test-source-bucket"
  source_hash          = "test-hash-2"
  function_source_dir  = "/tmp/test-source"
  
  function_name       = "user-activity-analysis-minimal"
  scheduler_job_name  = "user-activity-analysis-minimal-trigger"
  
  # Disable monitoring features for testing
  enable_scheduler_monitoring  = false
  enable_monitoring_alerts    = false
  enable_custom_metrics       = false
  enable_monitoring_dashboard = false
  
  notification_channels = []
}

# Test outputs for full monitoring
output "full_monitoring_dashboard" {
  description = "Full monitoring dashboard ID"
  value       = module.monitoring_test_full.monitoring_dashboard
}

output "full_alert_policies" {
  description = "Full monitoring alert policies"
  value = {
    function_errors    = module.monitoring_test_full.alert_policy_function_errors
    execution_time     = module.monitoring_test_full.alert_policy_execution_time
    scheduler_failures = module.monitoring_test_full.alert_policy_scheduler_failures
  }
}

output "full_custom_metrics" {
  description = "Full monitoring custom metrics"
  value = {
    completion_rate = module.monitoring_test_full.custom_metric_completion_rate
    errors         = module.monitoring_test_full.custom_metric_errors
  }
}

# Test outputs for minimal monitoring (should be null)
output "minimal_monitoring_dashboard" {
  description = "Minimal monitoring dashboard ID (should be null)"
  value       = module.monitoring_test_minimal.monitoring_dashboard
}

output "minimal_alert_policies" {
  description = "Minimal monitoring alert policies (should be null)"
  value = {
    function_errors    = module.monitoring_test_minimal.alert_policy_function_errors
    execution_time     = module.monitoring_test_minimal.alert_policy_execution_time
    scheduler_failures = module.monitoring_test_minimal.alert_policy_scheduler_failures
  }
}