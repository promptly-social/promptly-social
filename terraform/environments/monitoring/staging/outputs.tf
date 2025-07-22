# Standalone Monitoring Outputs - Staging

output "monitoring_summary" {
  description = "Summary of monitoring resources created"
  value       = module.monitoring.monitoring_summary
}

output "notification_channels" {
  description = "Created notification channels"
  value       = module.monitoring.notification_channels
  sensitive   = true
}

output "alert_policies" {
  description = "Created alert policies"
  value       = module.monitoring.alert_policies
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
