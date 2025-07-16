variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The environment (staging, production)"
  type        = string
}

variable "app_name" {
  description = "The application name"
  type        = string
  default     = "promptly-social"
}

variable "function_name" {
  description = "The name of the Cloud Function"
  type        = string
}

variable "function_source_dir" {
  description = "The directory containing the function source code"
  type        = string
}

variable "app_sa_email" {
  description = "The email of the application service account that can invoke this function"
  type        = string
}

variable "linkedin_token_refresh_threshold" {
  description = "Minutes before token expiry to refresh LinkedIn tokens"
  type        = number
  default     = 60
}

variable "max_retry_attempts" {
  description = "Maximum number of retry attempts for failed operations"
  type        = number
  default     = 3
}