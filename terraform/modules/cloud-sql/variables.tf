# Cloud SQL Module Variables

# Required variables
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud SQL instance"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., staging, production)"
  type        = string
}

variable "app_name" {
  description = "Application name for resource naming"
  type        = string
}

variable "terraform_sa_email" {
  description = "Email of the Terraform service account"
  type        = string
}

variable "app_sa_email" {
  description = "Email of the application service account"
  type        = string
}

# Instance configuration
variable "database_version" {
  description = "The PostgreSQL version to use"
  type        = string
  default     = "POSTGRES_15"
}

variable "tier" {
  description = "The machine type for the Cloud SQL instance"
  type        = string
  default     = "db-f1-micro"
}

variable "disk_size" {
  description = "The disk size in GB"
  type        = number
  default     = 20
}

variable "disk_type" {
  description = "The disk type (PD_SSD or PD_HDD)"
  type        = string
  default     = "PD_SSD"
}

variable "disk_autoresize" {
  description = "Enable automatic disk resize"
  type        = bool
  default     = true
}

variable "disk_autoresize_limit" {
  description = "Maximum disk size in GB for autoresize"
  type        = number
  default     = 100
}

variable "availability_type" {
  description = "Availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

# Backup configuration
variable "backup_enabled" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_start_time" {
  description = "Backup start time in HH:MM format"
  type        = string
  default     = "03:00"
}

variable "point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "backup_retention_count" {
  description = "Number of backups to retain"
  type        = number
  default     = 7
}

variable "transaction_log_retention_days" {
  description = "Number of days to retain transaction logs"
  type        = number
  default     = 7
}

# Maintenance window
variable "maintenance_window_day" {
  description = "Day of the week for maintenance (1-7, Monday is 1)"
  type        = number
  default     = 7
}

variable "maintenance_window_hour" {
  description = "Hour of the day for maintenance (0-23)"
  type        = number
  default     = 3
}

variable "maintenance_window_update_track" {
  description = "Update track for maintenance (canary or stable)"
  type        = string
  default     = "stable"
}

# Network configuration
variable "ipv4_enabled" {
  description = "Enable IPv4 for the instance"
  type        = bool
  default     = false
}

variable "private_network" {
  description = "VPC network for private IP"
  type        = string
  default     = null
}

variable "enable_private_path" {
  description = "Enable private path for Google Cloud services"
  type        = bool
  default     = true
}

variable "require_ssl" {
  description = "Require SSL connections"
  type        = bool
  default     = true
}

variable "authorized_networks" {
  description = "List of authorized networks"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

# Insights configuration
variable "query_insights_enabled" {
  description = "Enable query insights"
  type        = bool
  default     = true
}

variable "record_application_tags" {
  description = "Record application tags in insights"
  type        = bool
  default     = true
}

variable "record_client_address" {
  description = "Record client address in insights"
  type        = bool
  default     = true
}

# Cloud Function service accounts
variable "cloud_function_sa_emails" {
  description = "List of Cloud Function service account emails that need database access"
  type        = list(string)
  default     = []
}
