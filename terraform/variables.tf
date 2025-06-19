variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
  default     = "staging"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "promptly"
}

variable "docker_registry_location" {
  description = "Location for Docker registry"
  type        = string
  default     = "us-central1"
}

variable "cloud_run_min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 100
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run"
  type        = string
  default     = "2Gi"
}

variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "2"
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for resources"
  type        = bool
  default     = true
}

variable "cors_origins" {
  description = "CORS origins for the application"
  type        = list(string)
  default     = ["https://promptly.social"]
}

variable "github_repo" {
  description = "The GitHub repository in 'owner/repo' format (e.g., 'my-org/my-repo')"
  type        = string
}

variable "api_domain_name" {
  description = "The custom domain name for the API (e.g., 'api.yourdomain.com')"
  type        = string
}

variable "manage_cloud_run_service" {
  description = "If true, Terraform will manage the Cloud Run service. Set to false to manage it via a separate pipeline."
  type        = bool
  default     = false
} 