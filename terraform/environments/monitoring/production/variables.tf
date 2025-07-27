# Standalone Monitoring Variables - Production

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "promptly"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# Monitoring notification configuration
variable "monitoring_notification_emails" {
  description = "List of email addresses for monitoring alert notifications"
  type        = list(string)
  default     = []
}

variable "monitoring_slack_webhook_url" {
  description = "Slack webhook URL for monitoring notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

# Service monitoring toggles - Independent control
variable "enable_cloud_function_monitoring" {
  description = "Enable monitoring for Cloud Functions"
  type        = bool
  default     = true
}

variable "enable_cloud_run_monitoring" {
  description = "Enable monitoring for Cloud Run services"
  type        = bool
  default     = true
}

variable "enable_cloud_sql_monitoring" {
  description = "Enable monitoring for Cloud SQL"
  type        = bool
  default     = true
}

variable "enable_cloud_scheduler_monitoring" {
  description = "Enable monitoring for Cloud Scheduler"
  type        = bool
  default     = true
}

variable "enable_load_balancer_monitoring" {
  description = "Enable monitoring for Load Balancers"
  type        = bool
  default     = true
}

# Monitoring feature toggles
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

variable "enable_monitoring_dashboards" {
  description = "Enable monitoring dashboards"
  type        = bool
  default     = true
}

# Endpoint configuration - Independent of infrastructure
variable "api_endpoint" {
  description = "API endpoint URL for uptime checks"
  type        = string
  default     = "https://api.promptly.social"
}

variable "frontend_endpoint" {
  description = "Frontend endpoint URL for uptime checks"
  type        = string
  default     = "https://promptly.social"
}

# Monitoring threshold variables - Production optimized
variable "monitoring_cloud_function_error_threshold" {
  description = "Threshold for Cloud Function error rate alerts (errors per second)"
  type        = number
  default     = 0.05  # Strict for production
}

variable "monitoring_cloud_function_execution_time_threshold_ms" {
  description = "Threshold for Cloud Function execution time alerts (milliseconds)"
  type        = number
  default     = 300000  # 5 minutes
}

variable "monitoring_cloud_run_error_threshold" {
  description = "Threshold for Cloud Run error rate alerts (errors per second)"
  type        = number
  default     = 0.5  # Low tolerance for production
}

variable "monitoring_cloud_run_latency_threshold_ms" {
  description = "Threshold for Cloud Run latency alerts (milliseconds)"
  type        = number
  default     = 3000  # 3 seconds
}

variable "monitoring_cloud_sql_cpu_threshold" {
  description = "Threshold for Cloud SQL CPU utilization alerts (percentage)"
  type        = number
  default     = 0.7  # 70%
}

variable "monitoring_cloud_sql_memory_threshold" {
  description = "Threshold for Cloud SQL memory utilization alerts (percentage)"
  type        = number
  default     = 0.8  # 80%
}

variable "monitoring_cloud_sql_connections_threshold" {
  description = "Threshold for Cloud SQL connections alerts (number of connections)"
  type        = number
  default     = 200  # Higher for production
}

variable "monitoring_cloud_scheduler_failure_threshold" {
  description = "Threshold for Cloud Scheduler failure alerts (failures per 10 minutes)"
  type        = number
  default     = 1  # Alert immediately in production
}

variable "monitoring_load_balancer_error_threshold" {
  description = "Threshold for Load Balancer error rate alerts (errors per second)"
  type        = number
  default     = 2.0  # Strict for production
}
