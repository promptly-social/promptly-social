terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # This configuration is meant for a one-time, local execution.
  # The backend is intentionally local.
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
}

module "bootstrap" {
  source = "../../modules/bootstrap"

  project_id                  = var.project_id
  github_repo                 = var.github_repo
  app_name                    = var.app_name
  environment                 = "production"
  terraform_state_bucket_name = "promptly-terraform-state"
} 