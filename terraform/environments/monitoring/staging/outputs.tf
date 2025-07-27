# Standalone Monitoring Outputs - Staging

output "monitoring_summary" {
  description = "Summary of monitoring resources created"
  value       = module.monitoring.monitoring_summary
}

output "email_notification_channels" {
  description = "Email notification channel IDs"
  value       = module.monitoring.email_notification_channels
}

output "slack_notification_channel" {
  description = "Slack notification channel ID (if configured)"
  value       = module.monitoring.slack_notification_channel
  sensitive   = true
}

output "all_notification_channels" {
  description = "All notification channel IDs"
  value       = module.monitoring.all_notification_channels
  sensitive   = true
}

# Alert Policy Outputs
output "cloud_function_alert_policies" {
  description = "Cloud Function alert policy names"
  value       = module.monitoring.cloud_function_alert_policies
}

output "cloud_run_alert_policies" {
  description = "Cloud Run alert policy names"
  value       = module.monitoring.cloud_run_alert_policies
}

output "cloud_sql_alert_policies" {
  description = "Cloud SQL alert policy names"
  value       = module.monitoring.cloud_sql_alert_policies
}

output "cloud_scheduler_alert_policies" {
  description = "Cloud Scheduler alert policy names"
  value       = module.monitoring.cloud_scheduler_alert_policies
}

output "load_balancer_alert_policies" {
  description = "Load Balancer alert policy names"
  value       = module.monitoring.load_balancer_alert_policies
}

output "uptime_check_alert_policies" {
  description = "Uptime check alert policy names"
  value       = module.monitoring.uptime_check_alert_policies
}

output "dashboards" {
  description = "Created monitoring dashboards"
  value       = module.monitoring.dashboards
}

output "uptime_checks" {
  description = "Created uptime checks"
  value       = module.monitoring.uptime_checks
}

output "custom_metrics" {
  description = "Created custom metrics"
  value       = module.monitoring.custom_metrics
}
