# Standalone Monitoring Configuration - Production Environment

# Project Configuration
project_id = "promptly-social"
region     = "us-central1"
app_name   = "promptly"
environment = "production"

# Monitoring Notifications - Production
monitoring_notification_emails = [
  "justin@promptly.social",
]

# Slack webhook for production alerts (recommended for immediate notifications)
# monitoring_slack_webhook_url = "https://hooks.slack.com/services/YOUR/PRODUCTION/WEBHOOK"

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
api_endpoint      = "https://api.promptly.social"
frontend_endpoint = "https://promptly.social"

# Monitoring Thresholds - Production (Strict for Production Reliability)
monitoring_cloud_function_error_threshold              = 0.05   # 0.05 errors/sec
monitoring_cloud_function_execution_time_threshold_ms  = 300000 # 5 minutes
monitoring_cloud_run_error_threshold                   = 0.5    # 0.5 errors/sec
monitoring_cloud_run_latency_threshold_ms              = 3000   # 3 seconds
monitoring_cloud_sql_cpu_threshold                     = 0.7    # 70%
monitoring_cloud_sql_memory_threshold                  = 0.8    # 80%
monitoring_cloud_sql_connections_threshold             = 200    # 200 connections
monitoring_cloud_scheduler_failure_threshold           = 1      # 1 failure per 10min
monitoring_load_balancer_error_threshold               = 2.0    # 2 errors/sec
