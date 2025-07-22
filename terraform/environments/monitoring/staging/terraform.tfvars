# Standalone Monitoring Configuration - Staging Environment

# Project Configuration
project_id = "promptly-social-staging"
region     = "us-central1"
app_name   = "promptly"
environment = "staging"

# Monitoring Notifications - Staging
monitoring_notification_emails = [
  "dev-team@promptly.social",
  "staging-alerts@promptly.social"
]

# Optional Slack webhook for staging alerts
# monitoring_slack_webhook_url = "https://hooks.slack.com/services/YOUR/STAGING/WEBHOOK"

# Service Monitoring Toggles - Independent Control
enable_cloud_function_monitoring  = true
enable_cloud_run_monitoring      = true
enable_cloud_sql_monitoring      = true
enable_cloud_scheduler_monitoring = true
enable_load_balancer_monitoring  = true

# Monitoring Features
enable_uptime_checks             = true
enable_custom_metrics            = true
enable_monitoring_dashboards     = true

# Endpoint Configuration - Independent of Infrastructure Deployment
api_endpoint      = "https://api.staging.promptly.social"
frontend_endpoint = "https://staging.promptly.social"

# Monitoring Thresholds - Staging (Relaxed for Development)
monitoring_cloud_function_error_threshold              = 0.2    # 0.2 errors/sec
monitoring_cloud_function_execution_time_threshold_ms  = 900000 # 15 minutes
monitoring_cloud_run_error_threshold                   = 2.0    # 2 errors/sec
monitoring_cloud_run_latency_threshold_ms              = 10000  # 10 seconds
monitoring_cloud_sql_cpu_threshold                     = 0.9    # 90%
monitoring_cloud_sql_memory_threshold                  = 0.95   # 95%
monitoring_cloud_sql_connections_threshold             = 50     # 50 connections
monitoring_cloud_scheduler_failure_threshold           = 3      # 3 failures per 10min
monitoring_load_balancer_error_threshold               = 10.0   # 10 errors/sec
