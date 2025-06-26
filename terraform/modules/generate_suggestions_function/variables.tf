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

variable "openrouter_temperature" {
  description = "The temperature setting for OpenRouter model requests."
  type        = number
  default     = 0.0
}

variable "openrouter_large_model_primary" {
  description = "The primary large OpenRouter model to use for posts generation."
  type        = string
  default     = "google/gemini-2.5-pro"
}

variable "openrouter_large_models_fallback" {
  description = "The fallback large OpenRouter models to use for posts generation."
  type        = list(string)
  default     = ["google/gemini-2.5-pro", "meta-llama/llama-4-maverick"]
}

variable "openrouter_large_model_temperature" {
  description = "The temperature setting for large OpenRouter model requests."
  type        = number
  default     = 0.7
} 