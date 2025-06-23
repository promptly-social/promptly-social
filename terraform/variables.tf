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
  description = "The minimum number of container instances for the Cloud Run service."
  type        = number
  default     = 1
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 100
}

variable "cloud_run_memory" {
  description = "Memory for the Cloud Run service"
  type        = string
  default     = "512Mi"
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
  description = "Boolean flag to indicate if cloud run service should be managed by this Terraform config."
  type        = bool
  default     = true
}

variable "allow_unauthenticated_invocations" {
  description = "If true, allows unauthenticated invocations to the Cloud Run service."
  type        = bool
  default     = true
}

# Frontend Domain Name
variable "frontend_domain_name" {
  description = "The custom domain name for the frontend (e.g., 'yourdomain.com')"
  type        = string
}

variable "manage_frontend_infra" {
  description = "If true, Terraform will manage the frontend infrastructure (GCS bucket, CDN, etc.)."
  type        = bool
  default     = true
}

variable "production_project_id" {
  description = "The project ID of the production environment. Required for non-production environments to manage DNS."
  type        = string
  default     = null
}

variable "dns_editor_service_accounts" {
  description = "A list of service accounts to grant DNS editor role in the production project"
  type        = list(string)
  default     = []
}

variable "terraform_state_reader_service_accounts" {
  description = "A list of service accounts to grant read-only access to the terraform state bucket."
  type        = list(string)
  default     = []
}

variable "manage_backend_load_balancer" {
  description = "Boolean flag to indicate if the backend load balancer infrastructure should be managed."
  type        = bool
  default     = true
}

variable "dns_reader_service_accounts" {
  description = "A list of service accounts to grant DNS reader role in the production project"
  type        = list(string)
  default     = []
}

variable "dns_admin_service_accounts" {
  description = "A list of service accounts to grant DNS admin role in the production project"
  type        = list(string)
  default     = []
}

variable "image_tag" {
  description = "The Docker image tag to deploy."
  type        = string
  default     = "latest"
}

variable "terraform_service_account_email" {
  description = "The email of the service account used by Terraform to apply changes."
  type        = string
}