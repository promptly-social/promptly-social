# --- Outputs ---
# These values will be used to configure GitHub secrets for your CI/CD pipelines.

# Service Account outputs
output "terraform_service_account_email" {
  description = "Email of the Terraform service account for CI/CD operations"
  value       = google_service_account.terraform_sa.email
}

output "terraform_service_account_name" {
  description = "Full resource name of the Terraform service account"
  value       = google_service_account.terraform_sa.name
}

output "app_service_account_email" {
  description = "Email of the application service account for runtime operations"
  value       = google_service_account.app_sa.email
}

output "app_service_account_name" {
  description = "Full resource name of the application service account"
  value       = google_service_account.app_sa.name
}

# Workload Identity Federation outputs
output "workload_identity_pool_name" {
  description = "Full resource name of the Workload Identity Pool"
  value       = google_iam_workload_identity_pool.github_pool.name
}

output "workload_identity_pool_id" {
  description = "ID of the Workload Identity Pool"
  value       = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
}

output "workload_identity_pool_provider_name" {
  description = "Full resource name of the Workload Identity Pool Provider"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "workload_identity_pool_provider_id" {
  description = "ID of the Workload Identity Pool Provider"
  value       = google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id
}

# Infrastructure outputs
output "terraform_state_bucket_name" {
  description = "Name of the Terraform state bucket"
  value       = google_storage_bucket.terraform_state.name
}

output "terraform_state_bucket_url" {
  description = "URL of the Terraform state bucket"
  value       = google_storage_bucket.terraform_state.url
}

# Project information
output "project_id" {
  description = "The project ID where resources were created"
  value       = var.project_id
}

output "project_number" {
  description = "The project number"
  value       = data.google_project.project.number
}