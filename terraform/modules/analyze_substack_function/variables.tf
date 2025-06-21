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

variable "function_name" {
  description = "The name of the Cloud Function."
  type        = string
  default     = "analyze-substack"
}

variable "max_posts_to_analyze" {
  description = "The maximum number of posts to analyze."
  type        = number
  default     = 10
}

variable "environment" {
  description = "The deployment environment (e.g., staging, production)."
  type        = string
  default     = "staging"
}

variable "function_source_dir" {
  description = "The source directory of the cloud function."
  type        = string
} 