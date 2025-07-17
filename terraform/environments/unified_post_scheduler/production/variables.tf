variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "promptly-social"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The environment"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "The application name"
  type        = string
  default     = "promptly"
}

variable "function_name" {
  description = "The name of the unified post scheduler Cloud Function"
  type        = string
  default     = "unified-post-scheduler-production"
}

variable "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job"
  type        = string
  default     = "unified-post-scheduler-trigger-production"
}

variable "service_account_email" {
  description = "The email of the service account for function execution"
  type        = string
  default     = "promptly-app-sa-production@promptly-social.iam.gserviceaccount.com"
}