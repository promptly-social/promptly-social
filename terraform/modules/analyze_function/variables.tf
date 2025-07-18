variable "service_account_email" {
  description = "The email of the service account that will run this function."
  type        = string
}

variable "source_bucket" {
  description = "The name of the GCS bucket to store function source code."
  type        = string
}

variable "source_hash" {
  description = "Hash of the source code for versioning."
  type        = string
}

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
  default     = 5
}

variable "max_posts_to_analyze_linkedin" {
  description = "The maximum number of LinkedIn posts to analyze."
  type        = number
  default     = 20
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

variable "openrouter_model_primary" {
  description = "The primary OpenRouter model to use for analysis."
  type        = string
  default     = "google/gemini-2.5-flash-preview-05-20"
}

variable "openrouter_models_fallback" {
  description = "The fallback OpenRouter models to use for analysis."
  type        = list(string)
  default     = ["google/gemini-2.5-flash", "meta-llama/llama-4-maverick"]
}

variable "openrouter_model_temperature" {
  description = "The temperature setting for OpenRouter model requests."
  type        = number
  default     = 0.0
} 