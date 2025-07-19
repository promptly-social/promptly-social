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

# Generate source hash for versioning
locals {
  source_hash = substr(sha256(join("", [
    for f in fileset("${path.module}/../../../src/gcp-functions/generate_suggestions", "**") :
    filesha256("${path.module}/../../../src/gcp-functions/generate_suggestions/${f}")
  ])), 0, 8)
}

module "generate_suggestions_function" {
  source                             = "../../../modules/generate_suggestions_function"
  
  # New required variables for standardized pattern
  service_account_email              = "${var.app_name}-app-sa-${var.environment}@${var.project_id}.iam.gserviceaccount.com"
  source_bucket                      = "${var.app_name}-cf-source-${var.environment}"
  source_hash                        = local.source_hash
  
  # Existing variables
  project_id                         = var.project_id
  region                             = var.region
  app_name                           = var.app_name
  environment                        = var.environment
  function_name                      = "generate-suggestions-function-${var.environment}"
  function_source_dir                = "../../../src/gcp-functions"
  number_of_posts_to_generate        = var.number_of_posts_to_generate
  openrouter_model_primary           = var.openrouter_model_primary
  openrouter_models_fallback         = var.openrouter_models_fallback
  openrouter_model_temperature       = var.openrouter_model_temperature
  openrouter_large_model_primary     = var.openrouter_large_model_primary
  openrouter_large_models_fallback   = var.openrouter_large_models_fallback
  openrouter_large_model_temperature = var.openrouter_large_model_temperature
}

output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = module.generate_suggestions_function.function_uri
}

output "function_name" {
  description = "The name of the deployed Cloud Function."
  value       = module.generate_suggestions_function.function_name
} 