terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # This configuration is meant for a one-time, local execution.
  # The backend is intentionally local.
  backend "local" {}
}

provider "google" {
  project = var.project_id
}

module "bootstrap" {
  source = "../../../modules/bootstrap"

  project_id                  = var.project_id
  staging_project_id          = var.staging_project_id
  github_repo                 = var.github_repo
  app_name                    = var.app_name
  environment                 = "production"
  terraform_state_bucket_name = "promptly-terraform-states"
  dns_reader_service_accounts = [
    "promptly-tf-sa-staging@promptly-social-staging.iam.gserviceaccount.com"
  ]
  bootstrap_admins            = var.bootstrap_admins
} 