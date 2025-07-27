# Notification channel outputs
output "email_notification_channels" {
  description = "Email notification channel IDs"
  value       = google_monitoring_notification_channel.email[*].id
}

output "slack_notification_channel" {
  description = "Slack notification channel ID (if configured)"
  value       = var.slack_webhook_url != "" ? google_monitoring_notification_channel.slack[0].id : null
}

output "all_notification_channels" {
  description = "All notification channel IDs"
  value = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

# Alert policy outputs
output "cloud_function_alert_policies" {
  description = "Cloud Function alert policy names"
  value = {
    errors        = var.enable_cloud_function_monitoring ? google_monitoring_alert_policy.cloud_function_errors[0].name : null
    execution_time = var.enable_cloud_function_monitoring ? google_monitoring_alert_policy.cloud_function_execution_time[0].name : null
  }
}

output "cloud_run_alert_policies" {
  description = "Cloud Run alert policy names"
  value = {
    errors  = var.enable_cloud_run_monitoring ? google_monitoring_alert_policy.cloud_run_errors[0].name : null
    latency = var.enable_cloud_run_monitoring ? google_monitoring_alert_policy.cloud_run_latency[0].name : null
  }
}

output "cloud_sql_alert_policies" {
  description = "Cloud SQL alert policy names"
  value = {
    cpu         = var.enable_cloud_sql_monitoring ? google_monitoring_alert_policy.cloud_sql_cpu[0].name : null
    memory      = var.enable_cloud_sql_monitoring ? google_monitoring_alert_policy.cloud_sql_memory[0].name : null
    connections = var.enable_cloud_sql_monitoring ? google_monitoring_alert_policy.cloud_sql_connections[0].name : null
  }
}

output "cloud_scheduler_alert_policies" {
  description = "Cloud Scheduler alert policy names"
  value = {
    failures = var.enable_cloud_scheduler_monitoring ? google_monitoring_alert_policy.cloud_scheduler_failures[0].name : null
  }
}

output "load_balancer_alert_policies" {
  description = "Load Balancer alert policy names"
  value = {
    errors = var.enable_load_balancer_monitoring ? google_monitoring_alert_policy.load_balancer_errors[0].name : null
  }
}

output "uptime_check_alert_policies" {
  description = "Uptime check alert policy names"
  value = {
    failures = var.enable_uptime_checks ? google_monitoring_alert_policy.uptime_check_failures[0].name : null
  }
}

# Custom metrics outputs
output "custom_metrics" {
  description = "Custom logging metric names"
  value = {
    application_errors                = var.enable_custom_metrics ? google_logging_metric.application_errors[0].name : null
    user_activity_analysis_completion = var.enable_custom_metrics ? google_logging_metric.user_activity_analysis_completion[0].name : null
  }
}

# Uptime check outputs
output "uptime_checks" {
  description = "Uptime check configuration names"
  value = {
    api      = var.enable_uptime_checks && var.api_endpoint != "" ? google_monitoring_uptime_check_config.api_uptime[0].name : null
    frontend = var.enable_uptime_checks && var.frontend_endpoint != "" ? google_monitoring_uptime_check_config.frontend_uptime[0].name : null
  }
}

# Dashboard outputs
output "dashboards" {
  description = "Dashboard IDs"
  value = {
    system_overview = var.enable_dashboards ? google_monitoring_dashboard.system_overview[0].id : null
    cloud_functions = var.enable_dashboards && var.enable_cloud_function_monitoring ? google_monitoring_dashboard.cloud_functions[0].id : null
    cloud_run      = var.enable_dashboards && var.enable_cloud_run_monitoring ? google_monitoring_dashboard.cloud_run[0].id : null
    cloud_sql      = var.enable_dashboards && var.enable_cloud_sql_monitoring ? google_monitoring_dashboard.cloud_sql[0].id : null
  }
}

# Summary outputs for easy integration
output "monitoring_summary" {
  description = "Summary of monitoring resources created"
  value = {
    notification_channels_count = length(google_monitoring_notification_channel.email) + length(google_monitoring_notification_channel.slack)
    alert_policies_count = (
      (var.enable_cloud_function_monitoring ? 2 : 0) +
      (var.enable_cloud_run_monitoring ? 2 : 0) +
      (var.enable_cloud_sql_monitoring ? 3 : 0) +
      (var.enable_cloud_scheduler_monitoring ? 1 : 0) +
      (var.enable_load_balancer_monitoring ? 1 : 0) +
      (var.enable_uptime_checks ? 1 : 0)
    )
    custom_metrics_count = var.enable_custom_metrics ? 2 : 0
    uptime_checks_count = (
      (var.enable_uptime_checks && var.api_endpoint != "" ? 1 : 0) +
      (var.enable_uptime_checks && var.frontend_endpoint != "" ? 1 : 0)
    )
    dashboards_count = var.enable_dashboards ? 4 : 0
  }
}
