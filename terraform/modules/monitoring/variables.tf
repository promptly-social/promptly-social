variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., staging, production)"
  type        = string
}

# Notification configuration
variable "notification_emails" {
  description = "List of email addresses for alert notifications"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

# Monitoring feature toggles
variable "enable_cloud_function_monitoring" {
  description = "Enable Cloud Function monitoring and alerts"
  type        = bool
  default     = true
}

variable "enable_cloud_run_monitoring" {
  description = "Enable Cloud Run monitoring and alerts"
  type        = bool
  default     = true
}

variable "enable_cloud_sql_monitoring" {
  description = "Enable Cloud SQL monitoring and alerts"
  type        = bool
  default     = true
}

variable "enable_cloud_scheduler_monitoring" {
  description = "Enable Cloud Scheduler monitoring and alerts"
  type        = bool
  default     = true
}

variable "enable_load_balancer_monitoring" {
  description = "Enable Load Balancer monitoring and alerts"
  type        = bool
  default     = true
}

variable "enable_uptime_checks" {
  description = "Enable uptime checks for critical endpoints"
  type        = bool
  default     = true
}

variable "enable_custom_metrics" {
  description = "Enable custom logging metrics"
  type        = bool
  default     = true
}

variable "enable_dashboards" {
  description = "Enable monitoring dashboards"
  type        = bool
  default     = true
}

# Cloud Function monitoring thresholds
variable "cloud_function_error_threshold" {
  description = "Threshold for Cloud Function error rate alerts (errors per second)"
  type        = number
  default     = 0.1
}

variable "cloud_function_execution_time_threshold_ms" {
  description = "Threshold for Cloud Function execution time alerts (milliseconds)"
  type        = number
  default     = 600000  # 10 minutes
}

# Cloud Run monitoring thresholds
variable "cloud_run_error_threshold" {
  description = "Threshold for Cloud Run error rate alerts (errors per second)"
  type        = number
  default     = 1.0
}

variable "cloud_run_latency_threshold_ms" {
  description = "Threshold for Cloud Run latency alerts (milliseconds)"
  type        = number
  default     = 5000  # 5 seconds
}

# Cloud SQL monitoring thresholds
variable "cloud_sql_cpu_threshold" {
  description = "Threshold for Cloud SQL CPU utilization alerts (percentage)"
  type        = number
  default     = 0.8  # 80%
}

variable "cloud_sql_memory_threshold" {
  description = "Threshold for Cloud SQL memory utilization alerts (percentage)"
  type        = number
  default     = 0.9  # 90%
}

variable "cloud_sql_connections_threshold" {
  description = "Threshold for Cloud SQL connections alerts (number of connections)"
  type        = number
  default     = 80
}

# Cloud Scheduler monitoring thresholds
variable "cloud_scheduler_failure_threshold" {
  description = "Threshold for Cloud Scheduler failure alerts (failures per 10 minutes)"
  type        = number
  default     = 2
}

# Load Balancer monitoring thresholds
variable "load_balancer_error_threshold" {
  description = "Threshold for Load Balancer error rate alerts (errors per second)"
  type        = number
  default     = 5.0
}

# Uptime check configuration
variable "api_endpoint" {
  description = "API endpoint for uptime checks (without protocol)"
  type        = string
  default     = ""
}

variable "frontend_endpoint" {
  description = "Frontend endpoint for uptime checks (without protocol)"
  type        = string
  default     = ""
}

variable "api_health_check_path" {
  description = "Path for API health check"
  type        = string
  default     = "/health"
}

variable "api_health_check_response" {
  description = "Expected response content for API health check"
  type        = string
  default     = "ok"
}

# Dashboard configuration
variable "dashboard_time_range" {
  description = "Default time range for dashboard widgets"
  type        = string
  default     = "3600s"  # 1 hour
}

# Resource identifiers for monitoring (optional - for more specific filtering)
variable "cloud_function_names" {
  description = "List of Cloud Function names to monitor specifically"
  type        = list(string)
  default     = []
}

variable "cloud_run_service_names" {
  description = "List of Cloud Run service names to monitor specifically"
  type        = list(string)
  default     = []
}

variable "cloud_sql_instance_ids" {
  description = "List of Cloud SQL instance IDs to monitor specifically"
  type        = list(string)
  default     = []
}

variable "cloud_scheduler_job_names" {
  description = "List of Cloud Scheduler job names to monitor specifically"
  type        = list(string)
  default     = []
}
