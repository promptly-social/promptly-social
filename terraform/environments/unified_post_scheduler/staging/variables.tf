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
  default     = "promptly"
}

variable "function_name" {
  description = "The name of the unified post scheduler Cloud Function"
  type        = string
  default     = "unified-post-scheduler-staging"
}

variable "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job"
  type        = string
  default     = "unified-post-scheduler-trigger-staging"
}

variable "service_account_email" {
  description = "The email of the service account for function execution"
  type        = string
  default     = "promptly-app-sa-staging@promptly-social-staging.iam.gserviceaccount.com"
}