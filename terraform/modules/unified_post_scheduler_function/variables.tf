variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "function_name" {
  description = "Name of the unified post scheduler Cloud Function"
  type        = string
  default     = "unified-post-scheduler"
}

variable "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  type        = string
  default     = "unified-post-scheduler-trigger"
}

variable "region" {
  description = "GCP region for the function"
  type        = string
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