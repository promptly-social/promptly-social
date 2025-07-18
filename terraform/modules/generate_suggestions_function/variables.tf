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
  description = "The GCP region for the function."
  type        = string
}

variable "function_name" {
  description = "The name of the Cloud Function."
  type        = string
}

variable "function_source_dir" {
  description = "The source directory of the function code."
  type        = string
}

variable "app_name" {
  description = "The name of the application."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., staging, production)."
  type        = string
}

variable "number_of_posts_to_generate" {
  description = "Number of posts to generate."
  type        = string
  default     = "5"
}

variable "openrouter_model_primary" {
  description = "Primary OpenRouter model for generation."
  type        = string
  default     = "anthropic/claude-3-haiku"
}

variable "openrouter_models_fallback" {
  description = "Fallback OpenRouter models for generation."
  type        = list(string)
  default     = ["google/gemini-pro", "mistralai/mistral-7b-instruct"]
}

variable "openrouter_model_temperature" {
  description = "Temperature for OpenRouter model."
  type        = string
  default     = "0.7"
}

variable "openrouter_large_model_primary" {
  description = "Primary OpenRouter large model."
  type        = string
  default     = "anthropic/claude-3-opus"
}

variable "openrouter_large_models_fallback" {
  description = "Fallback OpenRouter large models."
  type        = list(string)
  default     = ["openai/gpt-4-turbo", "google/gemini-1.5-pro"]
}

variable "openrouter_large_model_temperature" {
  description = "Temperature for OpenRouter large model."
  type        = string
  default     = "0.5"
} 