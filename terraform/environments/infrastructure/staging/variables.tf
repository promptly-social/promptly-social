# Staging Environment Variables

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
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "promptly"
}

variable "production_project_id" {
  description = "The project ID of the production environment (for DNS management)"
  type        = string
}

variable "docker_registry_location" {
  description = "Location for Docker registry"
  type        = string
  default     = "us-central1"
}

variable "cloud_run_min_instances" {
  description = "The minimum number of container instances for the Cloud Run service"
  type        = number
  default     = 0
}

variable "terraform_state_reader_service_accounts" {
  description = "List of service accounts that should have read access to the Terraform state"
  type        = list(string)
  default     = []
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 2
}

variable "cloud_run_memory" {
  description = "Memory for the Cloud Run service"
  type        = string
  default     = "1Gi"
}

variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run"
  type        = string
  default     = "1000m"
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for resources"
  type        = bool
  default     = false
}

variable "github_repo" {
  description = "The GitHub repository in 'owner/repo' format"
  type        = string
}

variable "api_domain_name" {
  description = "The custom domain name for the API"
  type        = string
}

variable "frontend_domain_name" {
  description = "The custom domain name for the frontend"
  type        = string
}

variable "manage_cloud_run_service" {
  description = "Boolean flag to indicate if cloud run service should be managed"
  type        = bool
  default     = true
}

variable "cors_origins" {
  description = "CORS origins for the application"
  type        = list(string)
  default     = []  # Will use the default from the infrastructure module
}

variable "allow_unauthenticated_invocations" {
  description = "If true, allows unauthenticated invocations to the Cloud Run service"
  type        = bool
  default     = true
}

variable "manage_frontend_infra" {
  description = "If true, Terraform will manage the frontend infrastructure"
  type        = bool
  default     = true
}

variable "manage_backend_load_balancer" {
  description = "Boolean flag to indicate if the backend load balancer infrastructure should be managed"
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "The Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "terraform_service_account_email" {
  description = "The email of the service account used by Terraform to apply changes"
  type        = string
}

variable "manage_dns_zone" {
  description = "Whether to manage the DNS zone in this environment. Set to false to use an existing DNS zone."
  type        = bool
  default     = false
}

# Cloud SQL Configuration Variables
variable "cloud_sql_tier" {
  description = "The machine type for the Cloud SQL instance"
  type        = string
  default     = "db-f1-micro"
}

variable "cloud_sql_disk_size" {
  description = "The disk size in GB for the Cloud SQL instance"
  type        = number
  default     = 20
}

variable "cloud_sql_disk_autoresize_limit" {
  description = "Maximum disk size in GB for autoresize"
  type        = number
  default     = 100
}

variable "cloud_sql_availability_type" {
  description = "Availability type for Cloud SQL (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}

variable "cloud_sql_deletion_protection" {
  description = "Enable deletion protection for Cloud SQL instance"
  type        = bool
  default     = true
}

variable "cloud_sql_backup_retention_count" {
  description = "Number of backups to retain for Cloud SQL"
  type        = number
  default     = 7
}

variable "vpc_network" {
  description = "VPC network for private IP configuration"
  type        = string
  default     = null
}

variable "cloud_sql_transaction_log_retention_days" {
  description = "Number of days to retain transaction logs"
  type        = number
  default     = 7
}

variable "cloud_sql_authorized_networks" {
  description = "List of authorized networks for Cloud SQL"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "cloud_function_sa_emails" {
  description = "List of Cloud Function service account emails that need database access"
  type        = list(string)
  default     = []
}
