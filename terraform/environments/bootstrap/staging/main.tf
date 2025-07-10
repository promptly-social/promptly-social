terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "local" {}
}

provider "google" {
  project = var.project_id
}

module "bootstrap" {
  source = "../../../modules/bootstrap"

  project_id                  = var.project_id
  github_repo                 = var.github_repo
  app_name                    = var.app_name
  environment                 = "staging"
  terraform_state_bucket_name = "promptly-terraform-states"
  bootstrap_admins            = var.bootstrap_admins
} 