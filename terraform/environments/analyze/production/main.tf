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
    for f in fileset("${path.module}/../../../src/gcp-functions/unified-post-scheduler", "**") :
    filesha256("${path.module}/../../../src/gcp-functions/unified-post-scheduler/${f}")
  ])), 0, 8)
}

module "analyze_function" {
  source                        = "../../../modules/analyze_function"
  
  # New required variables for standardized pattern
  service_account_email         = "promptly-app-sa-production@${var.project_id}.iam.gserviceaccount.com"
  source_bucket                 = "promptly-cf-source-production"
  source_hash                   = local.source_hash
  
  # Existing variables
  project_id                    = var.project_id
  region                        = var.region
  environment                   = "production"
  function_source_dir           = "../../../src/gcp-functions"
  max_posts_to_analyze          = 10
  max_posts_to_analyze_linkedin = 20
  openrouter_model_primary      = "google/gemini-2.5-flash-preview-05-20"
  openrouter_models_fallback    = ["google/gemini-2.5-flash", "meta-llama/llama-4-maverick"]
  openrouter_model_temperature  = 0.0
}

output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = module.analyze_function.function_uri
}

output "function_name" {
  description = "The name of the deployed Cloud Function."
  value       = module.analyze_function.function_name
} 