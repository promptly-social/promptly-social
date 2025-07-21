# Test configuration for user activity analysis function module
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Mock variables for testing
variable "project_id" {
  description = "Test project ID"
  type        = string
  default     = "test-project"
}

variable "region" {
  description = "Test region"
  type        = string
  default     = "us-central1"
}

variable "service_account_email" {
  description = "Test service account email"
  type        = string
  default     = "test-sa@test-project.iam.gserviceaccount.com"
}

variable "source_bucket" {
  description = "Test source bucket"
  type        = string
  default     = "test-source-bucket"
}

# Test the module
module "user_activity_analysis_function" {
  source = "../"

  project_id            = var.project_id
  region               = var.region
  service_account_email = var.service_account_email
  source_bucket        = var.source_bucket
  source_hash          = "test-hash"
  function_source_dir  = "/tmp/test-source"
  
  # Test with custom configuration
  schedule             = "0 */2 * * *"  # Every 2 hours for testing
  timezone            = "America/New_York"
  post_threshold      = 3
  message_threshold   = 8
  ai_provider         = "anthropic"
}

# Test outputs
output "test_function_uri" {
  description = "Test function URI"
  value       = module.user_activity_analysis_function.function_uri
}

output "test_function_name" {
  description = "Test function name"
  value       = module.user_activity_analysis_function.function_name
}

output "test_scheduler_job_name" {
  description = "Test scheduler job name"
  value       = module.user_activity_analysis_function.scheduler_job_name
}