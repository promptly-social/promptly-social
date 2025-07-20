output "function_uri" {
  description = "The URI of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.service_config[0].uri
}

output "function_name" {
  description = "The name of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.name
}

output "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.user_activity_analysis.name
}

output "scheduler_job_id" {
  description = "The ID of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.user_activity_analysis.id
}

output "scheduler_monitoring_topic" {
  description = "The Pub/Sub topic for scheduler monitoring (if enabled)"
  value       = var.enable_scheduler_monitoring ? google_pubsub_topic.scheduler_monitoring[0].name : null
}

output "scheduler_log_sink" {
  description = "The log sink for scheduler monitoring (if enabled)"
  value       = var.enable_scheduler_monitoring ? google_logging_project_sink.scheduler_monitoring[0].name : null
}

# Monitoring outputs
output "alert_policy_function_errors" {
  description = "The function error rate alert policy (if enabled)"
  value       = var.enable_monitoring_alerts ? google_monitoring_alert_policy.function_error_rate[0].name : null
}

output "alert_policy_execution_time" {
  description = "The function execution time alert policy (if enabled)"
  value       = var.enable_monitoring_alerts ? google_monitoring_alert_policy.function_execution_time[0].name : null
}

output "alert_policy_scheduler_failures" {
  description = "The scheduler failure alert policy (if enabled)"
  value       = var.enable_monitoring_alerts ? google_monitoring_alert_policy.scheduler_job_failures[0].name : null
}

output "custom_metric_completion_rate" {
  description = "The analysis completion rate custom metric (if enabled)"
  value       = var.enable_custom_metrics ? google_logging_metric.analysis_completion_rate[0].name : null
}

output "custom_metric_errors" {
  description = "The analysis errors custom metric (if enabled)"
  value       = var.enable_custom_metrics ? google_logging_metric.analysis_errors[0].name : null
}

output "monitoring_dashboard" {
  description = "The monitoring dashboard (if enabled)"
  value       = var.enable_monitoring_dashboard ? google_monitoring_dashboard.user_activity_analysis[0].id : null
}