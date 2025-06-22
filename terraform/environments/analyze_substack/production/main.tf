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

module "analyze_substack_function" {
  source                = "../../../modules/analyze_substack_function"
  project_id            = var.project_id
  region                = var.region
  environment           = "production"
  function_source_dir   = "../../../src/gcp-functions/analyze-substack"
  max_posts_to_analyze  = 10
}

output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = module.analyze_substack_function.function_uri
}

output "function_url_secret_version" {
  description = "The version of the secret containing the function URL."
  value       = module.analyze_substack_function.function_url_secret_version
} 