variable "gcp_analysis_function_url_version" {
  description = "The version of the GCP analysis function URL secret, to trigger updates."
  type        = string
}

variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Run service."
  type        = string
}

variable "app_name" {
  description = "The name of the application."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., 'staging', 'production')."
  type        = string
}

variable "cloud_run_min_instances" {
  description = "The minimum number of container instances for Cloud Run."
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "The maximum number of container instances for Cloud Run."
  type        = number
  default     = 2
}

variable "cloud_run_cpu" {
  description = "The CPU limit for the Cloud Run container."
  type        = string
  default     = "1000m"
}

variable "cloud_run_memory" {
  description = "The memory limit for the Cloud Run container."
  type        = string
  default     = "512Mi"
}

variable "service_account_email" {
  description = "The email of the service account for the Cloud Run service."
  type        = string
}

variable "docker_registry_location" {
  description = "The location of the Docker Artifact Registry."
  type        = string
}

variable "backend_repo_repository_id" {
  description = "The repository ID of the backend container image."
  type        = string
}

variable "gcp_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "gcp_location" {
  description = "The GCP location."
  type        = string
}

variable "cors_origins" {
  description = "A list of allowed CORS origins."
  type        = list(string)
}

variable "jwt_secret_name" {
  description = "The name of the Secret Manager secret for the JWT secret key."
  type        = string
}

variable "supabase_url_name" {
  description = "The name of the Secret Manager secret for the Supabase URL."
  type        = string
}

variable "supabase_key_name" {
  description = "The name of the Secret Manager secret for the Supabase key."
  type        = string
}

variable "supabase_service_key_name" {
  description = "The name of the Secret Manager secret for the Supabase service key."
  type        = string
}

variable "google_client_id_name" {
  description = "The name of the Secret Manager secret for the Google Client ID."
  type        = string
}

variable "google_client_secret_name" {
  description = "The name of the Secret Manager secret for the Google Client Secret."
  type        = string
}

variable "gcp_analysis_function_url_name" {
  description = "The name of the Secret Manager secret for the GCP analysis function URL"
  type        = string
}

variable "openrouter_api_key_name" {
  description = "The name of the Secret Manager secret for the OpenRouter API key"
  type        = string
}

variable "image_tag" {
  description = "The tag for the container image to deploy."
  type        = string
  default     = "latest"
}

variable "enable_public_access" {
  description = "Flag to enable public access to the Cloud Run service"
  type        = bool
  default     = true
}

variable "allow_unauthenticated_invocations" {
  description = "If true, allows unauthenticated invocations to the Cloud Run service."
  type        = bool
  default     = true
}

variable "frontend_url" {
  description = "The URL of the frontend application."
  type        = string
}

variable "backend_url" {
  description = "The URL of the backend application."
  type        = string
}

variable "linkedin_client_id_name" {
  description = "The name of the Secret Manager secret for the LinkedIn Client ID."
  type        = string
}

variable "linkedin_client_secret_name" {
  description = "The name of the Secret Manager secret for the LinkedIn Client Secret."
  type        = string
}

variable "database_url_name" {
  description = "The name of the Secret Manager secret for the database URL."
  type        = string
}

variable "openrouter_model_primary_name" {
  description = "The name of the Secret Manager secret for the OpenRouter model primary."
  type        = string
}

variable "openrouter_models_fallback_name" {
  description = "The name of the Secret Manager secret for the OpenRouter models fallback."
  type        = string
}

variable "openrouter_model_temperature_name" {
  description = "The name of the Secret Manager secret for the OpenRouter model temperature."
  type        = string
}

variable "openrouter_large_model_primary_name" {
  description = "The name of the Secret Manager secret for the OpenRouter large model primary."
  type        = string
}

variable "openrouter_large_models_fallback_name" {
  description = "The name of the Secret Manager secret for the OpenRouter large models fallback."
  type        = string
}

variable "openrouter_large_model_temperature_name" {
  description = "The name of the Secret Manager secret for the OpenRouter large model temperature."
  type        = string
}