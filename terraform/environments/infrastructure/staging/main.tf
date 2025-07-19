# Staging Environment - Infrastructure Module
# This configuration deploys the infrastructure module for the staging environment

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9.1"
    }
  }
}

# Configure provider to use Application Default Credentials (ADC)
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Configure DNS provider for cross-project DNS management
provider "google" {
  alias   = "dns"
  project = var.production_project_id
  # Remove impersonation to use ADC directly
}

# Deploy the infrastructure module
module "infrastructure" {
  source = "../../../infrastructure"

  # Basic configuration
  project_id  = var.project_id
  region      = var.region
  zone        = var.zone
  environment = var.environment
  app_name    = var.app_name

  # Service account created by bootstrap
  terraform_service_account_email = var.terraform_service_account_email

  # Application configuration
  github_repo                       = var.github_repo
  frontend_domain_name             = var.frontend_domain_name
  api_domain_name                  = var.api_domain_name
  docker_registry_location         = var.docker_registry_location

  # Feature flags
  manage_cloud_run_service         = var.manage_cloud_run_service
  manage_frontend_infra            = var.manage_frontend_infra
  manage_backend_load_balancer     = var.manage_backend_load_balancer
  allow_unauthenticated_invocations = var.allow_unauthenticated_invocations

  # Cloud Run configuration (staging-optimized)
  cloud_run_min_instances = var.cloud_run_min_instances
  cloud_run_max_instances = var.cloud_run_max_instances
  cloud_run_memory        = var.cloud_run_memory
  cloud_run_cpu          = var.cloud_run_cpu

  # Cloud SQL configuration
  cloud_sql_tier                    = var.cloud_sql_tier
  cloud_sql_disk_size              = var.cloud_sql_disk_size
  cloud_sql_disk_autoresize_limit  = var.cloud_sql_disk_autoresize_limit
  cloud_sql_availability_type      = var.cloud_sql_availability_type
  cloud_sql_deletion_protection    = var.cloud_sql_deletion_protection
  cloud_sql_backup_retention_count = var.cloud_sql_backup_retention_count
  cloud_sql_transaction_log_retention_days = var.cloud_sql_transaction_log_retention_days
  cloud_sql_authorized_networks    = var.cloud_sql_authorized_networks
  cloud_function_sa_emails         = var.cloud_function_sa_emails
  vpc_network                      = var.vpc_network

  # Other configuration
  production_project_id       = var.production_project_id
  image_tag                  = var.image_tag
  enable_deletion_protection  = var.enable_deletion_protection
}
