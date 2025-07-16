variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "promptly-social-staging"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The environment"
  type        = string
  default     = "staging"
}

variable "app_name" {
  description = "The application name"
  type        = string
  default     = "promptly-social"
}

variable "function_name" {
  description = "The name of the Cloud Function"
  type        = string
  default     = "share-post-staging"
}

variable "function_source_dir" {
  description = "The directory containing the function source code"
  type        = string
  default     = "../../../src/gcp-functions/share-post"
}

variable "app_sa_email" {
  description = "The email of the application service account"
  type        = string
  default     = "promptly-social-app-sa-staging@promptly-social-staging.iam.gserviceaccount.com"
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