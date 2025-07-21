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

variable "environment" {
  description = "The deployment environment."
  type        = string
  default     = "staging"
}

variable "number_of_posts_to_generate" {
  description = "The number of posts to generate."
  type        = string
  default     = "5"
}

variable "openrouter_model_primary" {
  description = "The primary OpenRouter model to use for analysis."
  type        = string
  default     = "google/gemini-2.5-flash"
}

variable "openrouter_models_fallback" {
  description = "The fallback OpenRouter models to use for analysis."
  type        = list(string)
  default     = ["meta-llama/llama-4-maverick"]
}

variable "openrouter_model_temperature" {
  description = "The temperature setting for OpenRouter model requests."
  type        = string
  default     = "0.0"
}

variable "openrouter_large_model_primary" {
  description = "The primary large OpenRouter model to use for posts generation."
  type        = string
  default     = "google/gemini-2.5-pro"
}

variable "openrouter_large_models_fallback" {
  description = "The fallback large OpenRouter models to use for posts generation."
  type        = list(string)
  default     = ["deepseek/deepseek-r1-0528"]
}

variable "openrouter_large_model_temperature" {
  description = "The temperature setting for large OpenRouter model requests."
  type        = string
  default     = "0.0"
} 