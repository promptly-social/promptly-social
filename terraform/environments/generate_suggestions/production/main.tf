terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "generate_suggestions_function" {
  source                             = "../../../modules/generate_suggestions_function"
  project_id                         = var.project_id
  region                             = var.region
  app_name                           = var.app_name
  environment                        = var.environment
  function_name                      = "generate-suggestions-function-${var.environment}"
  function_source_dir                = "../../../src/gcp-functions/generate-suggestions"
  app_sa_email                       = "promptly-app-sa-${var.environment}@${var.project_id}.iam.gserviceaccount.com"
  number_of_posts_to_generate        = var.number_of_posts_to_generate
  openrouter_model_primary           = var.openrouter_model_primary
  openrouter_models_fallback         = var.openrouter_models_fallback
  openrouter_model_temperature             = var.openrouter_model_temperature
  openrouter_large_model_primary     = var.openrouter_large_model_primary
  openrouter_large_models_fallback   = var.openrouter_large_models_fallback
  openrouter_large_model_temperature = var.openrouter_large_model_temperature
}

output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = module.generate_suggestions_function.function_uri
}

output "function_url_secret_version" {
  description = "The version of the secret containing the function URL."
  value       = module.generate_suggestions_function.function_url_secret_version
} 