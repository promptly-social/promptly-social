output "gcp_project_id" {
  description = "The GCP Project ID."
  value       = module.bootstrap.gcp_project_id
}

output "workload_identity_provider" {
  description = "The full ID of the Workload Identity Provider for GitHub Actions."
  value       = module.bootstrap.workload_identity_provider
}

output "terraform_service_account_email" {
  description = "The email of the service account created for Terraform CI/CD."
  value       = module.bootstrap.terraform_service_account_email
}

output "terraform_state_bucket_name" {
  description = "The name of the GCS bucket for Terraform state."
  value       = module.bootstrap.terraform_state_bucket_name
} 