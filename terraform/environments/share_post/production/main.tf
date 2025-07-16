terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

module "share_post_function" {
  source = "../../../modules/share_post_function"

  project_id            = var.project_id
  region               = var.region
  environment          = var.environment
  app_name            = var.app_name
  function_name       = var.function_name
  function_source_dir = var.function_source_dir
  app_sa_email        = var.app_sa_email
  
  linkedin_token_refresh_threshold = var.linkedin_token_refresh_threshold
  max_retry_attempts              = var.max_retry_attempts
}