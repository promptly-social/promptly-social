variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy the function to."
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "The name of the application."
  type        = string
  default     = "promptly"
}

variable "environment" {
  description = "The deployment environment."
  type        = string
  default     = "production"
}

# Scheduler configuration - once daily at midnight PDT
variable "schedule" {
  description = "Cron schedule for the analysis job - once daily at midnight PDT"
  type        = string
  default     = "0 7 * * *"  # 7 AM UTC = midnight PDT (UTC-7)
}

variable "timezone" {
  description = "Timezone for the scheduler"
  type        = string
  default     = "America/Los_Angeles"  # PDT timezone
}

variable "scheduler_paused" {
  description = "Whether the scheduler job should be paused initially"
  type        = bool
  default     = false
}

# Analysis configuration
variable "openrouter_model_primary" {
  description = "Primary OpenRouter model for analysis."
  type        = string
  default     = "google/gemini-2.5-flash"
}

variable "openrouter_models_fallback" {
  description = "Fallback OpenRouter models for analysis."
  type        = list(string)
  default     = ["meta-llama/llama-4-maverick"]
}

variable "openrouter_model_temperature" {
  description = "Temperature for OpenRouter model."
  type        = string
  default     = "0.0"
}

variable "post_threshold" {
  description = "Minimum number of posts to trigger analysis"
  type        = number
  default     = 5  # Lower threshold for staging
}

variable "message_threshold" {
  description = "Minimum number of messages to trigger analysis"
  type        = number
  default     = 8  # Lower threshold for staging
}

variable "max_retry_attempts" {
  description = "Maximum retry attempts for failed operations"
  type        = number
  default     = 1
}

variable "analysis_timeout_minutes" {
  description = "Timeout for analysis operations in minutes"
  type        = number
  default     = 15
}

variable "batch_size" {
  description = "Number of users to process in each batch"
  type        = number
  default     = 5  # Smaller batch size for staging
}

# Monitoring configuration
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

variable "enable_scheduler_monitoring" {
  description = "Enable advanced monitoring for scheduler jobs"
  type        = bool
  default     = true
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# Alert thresholds (more lenient for staging)
variable "error_rate_threshold" {
  description = "Threshold for function error rate alerts (errors per second)"
  type        = number
  default     = 0.2  # More lenient for staging
}

variable "execution_time_threshold_ms" {
  description = "Threshold for function execution time alerts (milliseconds)"
  type        = number
  default     = 720000  # 12 minutes (more lenient for staging)
}

variable "scheduler_failure_threshold" {
  description = "Threshold for scheduler job failure alerts (failures per 10 minutes)"
  type        = number
  default     = 3  # More lenient for staging
}
