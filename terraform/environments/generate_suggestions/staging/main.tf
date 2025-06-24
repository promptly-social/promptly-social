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
  source                      = "../../../modules/generate_suggestions_function"
  project_id                  = var.project_id
  region                      = var.region
  environment                 = "staging"
  function_source_dir         = "../../../src/gcp-functions/generate-suggestions"
  number_of_posts_to_generate = 3
}

output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = module.generate_suggestions_function.function_uri
}

output "function_url_secret_version" {
  description = "The version of the secret containing the function URL."
  value       = module.generate_suggestions_function.function_url_secret_version
} 