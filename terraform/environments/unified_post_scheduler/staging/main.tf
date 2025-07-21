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

# Data source to get the existing source bucket
data "google_storage_bucket" "source_bucket" {
  name = "${var.app_name}-cf-source-${var.environment}"
}

# Generate source hash for versioning
locals {
  source_hash = substr(sha256(join("", concat([
    for f in fileset("${path.module}/../../../src/gcp-functions/user_activity_analysis", "**") :
    filesha256("${path.module}/../../../src/gcp-functions/user_activity_analysis/${f}")
  ], [
    for f in fileset("${path.module}/../../../src/gcp-functions/shared", "**") :
    filesha256("${path.module}/../../../src/gcp-functions/shared/${f}")
  ], [
    filesha256("${path.module}/../../../src/gcp-functions/main.py")
  ]))), 0, 8)
}

module "unified_post_scheduler_function" {
  source = "../../../modules/unified_post_scheduler_function"

  project_id           = var.project_id
  function_name        = var.function_name
  scheduler_job_name   = var.scheduler_job_name
  region              = var.region
  source_bucket       = data.google_storage_bucket.source_bucket.name
  source_hash         = local.source_hash
  service_account_email = var.service_account_email
}