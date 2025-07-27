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
  default     = 20
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

variable "manage_dns_zone" {
  description = "Whether to manage the DNS zone in this module"
  type        = bool
  default     = true
}

variable "manage_backend_load_balancer" {
  description = "Boolean flag to indicate if the backend load balancer infrastructure should be managed."
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "The Docker image tag to deploy."
  type        = string
  default     = "latest"
}

variable "terraform_service_account_email" {
  description = "Email of the Terraform service account created by bootstrap"
  type        = string
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

# Monitoring Configuration Variables
variable "monitoring_notification_emails" {
  description = "List of email addresses for monitoring alert notifications"
  type        = list(string)
  default     = []
}

variable "monitoring_slack_webhook_url" {
  description = "Slack webhook URL for monitoring notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

# Service management flags for monitoring
variable "manage_cloud_functions" {
  description = "Whether to manage Cloud Functions (enables function monitoring)"
  type        = bool
  default     = true
}

variable "manage_cloud_sql" {
  description = "Whether to manage Cloud SQL (enables SQL monitoring)"
  type        = bool
  default     = true
}

variable "manage_cloud_scheduler" {
  description = "Whether to manage Cloud Scheduler (enables scheduler monitoring)"
  type        = bool
  default     = true
}

variable "manage_frontend_deployment" {
  description = "Whether to manage frontend deployment (enables frontend uptime checks)"
  type        = bool
  default     = true
}

# Monitoring feature toggles
variable "enable_uptime_checks" {
  description = "Enable uptime checks for critical endpoints"
  type        = bool
  default     = true
}

variable "enable_custom_metrics" {
  description = "Enable custom logging metrics"
  type        = bool
  default     = true
}

variable "enable_monitoring_dashboards" {
  description = "Enable monitoring dashboards"
  type        = bool
  default     = true
}

# Monitoring threshold variables
variable "monitoring_cloud_function_error_threshold" {
  description = "Threshold for Cloud Function error rate alerts (errors per second)"
  type        = number
  default     = 0.1
}

variable "monitoring_cloud_function_execution_time_threshold_ms" {
  description = "Threshold for Cloud Function execution time alerts (milliseconds)"
  type        = number
  default     = 600000  # 10 minutes
}

variable "monitoring_cloud_run_error_threshold" {
  description = "Threshold for Cloud Run error rate alerts (errors per second)"
  type        = number
  default     = 1.0
}

variable "monitoring_cloud_run_latency_threshold_ms" {
  description = "Threshold for Cloud Run latency alerts (milliseconds)"
  type        = number
  default     = 5000  # 5 seconds
}

variable "monitoring_cloud_sql_cpu_threshold" {
  description = "Threshold for Cloud SQL CPU utilization alerts (percentage)"
  type        = number
  default     = 0.8  # 80%
}

variable "monitoring_cloud_sql_memory_threshold" {
  description = "Threshold for Cloud SQL memory utilization alerts (percentage)"
  type        = number
  default     = 0.9  # 90%
}

variable "monitoring_cloud_sql_connections_threshold" {
  description = "Threshold for Cloud SQL connections alerts (number of connections)"
  type        = number
  default     = 80
}

variable "monitoring_cloud_scheduler_failure_threshold" {
  description = "Threshold for Cloud Scheduler failure alerts (failures per 10 minutes)"
  type        = number
  default     = 2
}

variable "monitoring_load_balancer_error_threshold" {
  description = "Threshold for Load Balancer error rate alerts (errors per second)"
  type        = number
  default     = 5.0
}
