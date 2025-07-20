variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for the function"
  type        = string
  default     = "us-central1"
}

variable "function_name" {
  description = "Name of the user activity analysis Cloud Function"
  type        = string
  default     = "user-activity-analysis"
}

variable "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  type        = string
  default     = "user-activity-analysis-trigger"
}

variable "source_bucket" {
  description = "GCS bucket for storing function source code"
  type        = string
}

variable "source_hash" {
  description = "Hash of the source code for versioning"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for function execution"
  type        = string
}

variable "function_source_dir" {
  description = "The source directory of the function code"
  type        = string
}

variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "promptly"
}

variable "environment" {
  description = "The deployment environment (e.g., staging, production)"
  type        = string
  default     = "staging"
}

# Scheduler configuration
variable "schedule" {
  description = "Cron schedule for the analysis job"
  type        = string
  default     = "0 * * * *"  # Every hour at minute 0
}

variable "timezone" {
  description = "Timezone for the scheduler"
  type        = string
  default     = "UTC"
}

variable "scheduler_retry_count" {
  description = "Number of retry attempts for failed scheduler jobs"
  type        = number
  default     = 3
}

variable "scheduler_paused" {
  description = "Whether the scheduler job should be paused initially"
  type        = bool
  default     = false
}

variable "scheduler_max_retry_duration" {
  description = "Maximum duration for retrying failed scheduler jobs"
  type        = string
  default     = "1800s"  # 30 minutes
}

variable "scheduler_min_backoff_duration" {
  description = "Minimum backoff duration between retries"
  type        = string
  default     = "5s"
}

variable "scheduler_max_backoff_duration" {
  description = "Maximum backoff duration between retries"
  type        = string
  default     = "300s"  # 5 minutes
}

variable "scheduler_max_doublings" {
  description = "Maximum number of times to double the backoff duration"
  type        = number
  default     = 5
}

variable "enable_scheduler_monitoring" {
  description = "Enable advanced monitoring for scheduler jobs"
  type        = bool
  default     = true
}

# Monitoring and alerting configuration
variable "enable_monitoring_alerts" {
  description = "Enable Cloud Monitoring alert policies"
  type        = bool
  default     = true
}

variable "enable_custom_metrics" {
  description = "Enable custom logging metrics"
  type        = bool
  default     = true
}

variable "enable_monitoring_dashboard" {
  description = "Enable monitoring dashboard creation"
  type        = bool
  default     = true
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

variable "error_rate_threshold" {
  description = "Threshold for function error rate alerts (errors per second)"
  type        = number
  default     = 0.1
}

variable "execution_time_threshold_ms" {
  description = "Threshold for function execution time alerts (milliseconds)"
  type        = number
  default     = 600000  # 10 minutes
}

variable "scheduler_failure_threshold" {
  description = "Threshold for scheduler job failure alerts (failures per 10 minutes)"
  type        = number
  default     = 2
}

# Analysis configuration
variable "ai_provider" {
  description = "AI provider to use for analysis (openai, anthropic)"
  type        = string
  default     = "openai"
}

variable "post_threshold" {
  description = "Minimum number of posts to trigger analysis"
  type        = number
  default     = 5
}

variable "message_threshold" {
  description = "Minimum number of messages to trigger analysis"
  type        = number
  default     = 10
}

variable "max_retry_attempts" {
  description = "Maximum retry attempts for failed operations"
  type        = number
  default     = 3
}

variable "analysis_timeout_minutes" {
  description = "Timeout for analysis operations in minutes"
  type        = number
  default     = 15
}

variable "batch_size" {
  description = "Number of users to process in each batch"
  type        = number
  default     = 10
}