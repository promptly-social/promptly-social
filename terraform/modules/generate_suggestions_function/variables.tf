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
  default     = "generate-suggestions"
}

variable "number_of_posts_to_generate" {
  description = "The number of posts to generate."
  type        = number
  default     = 5
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