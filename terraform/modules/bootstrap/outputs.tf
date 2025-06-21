# --- Outputs ---
# These values will be used to configure GitHub secrets for your CI/CD pipelines.

output "gcp_project_id" {
  description = "The GCP Project ID."
  value       = var.project_id
}

output "workload_identity_provider" {
  description = "The full ID of the Workload Identity Provider for GitHub Actions."
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "terraform_service_account_email" {
  description = "The email of the service account created for Terraform CI/CD."
  value       = google_service_account.terraform_sa.email
}

output "terraform_state_bucket_name" {
  description = "The name of the GCS bucket for Terraform state."
  value       = google_storage_bucket.terraform_state.name
}

output "app_sa_email" {
  description = "The email of the application service account."
  value       = google_service_account.app_sa.email
} 