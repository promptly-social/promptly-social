output "terraform_service_account_email" {
  description = "Email of the Terraform service account for CI/CD operations"
  value       = module.bootstrap.terraform_service_account_email
}

output "terraform_service_account_name" {
  description = "Full resource name of the Terraform service account"
  value       = module.bootstrap.terraform_service_account_name
}

output "app_service_account_email" {
  description = "Email of the application service account for runtime operations"
  value       = module.bootstrap.app_service_account_email
}

output "app_service_account_name" {
  description = "Full resource name of the application service account"
  value       = module.bootstrap.app_service_account_name
}

output "workload_identity_pool_name" {
  description = "Full resource name of the Workload Identity Pool"
  value       = module.bootstrap.workload_identity_pool_name
}

output "workload_identity_pool_id" {
  description = "ID of the Workload Identity Pool"
  value       = module.bootstrap.workload_identity_pool_id
}

output "workload_identity_pool_provider_name" {
  description = "Full resource name of the Workload Identity Pool Provider"
  value       = module.bootstrap.workload_identity_pool_provider_name
}

output "workload_identity_pool_provider_id" {
  description = "ID of the Workload Identity Pool Provider"
  value       = module.bootstrap.workload_identity_pool_provider_id
}

output "terraform_state_bucket_name" {
  description = "Name of the Terraform state bucket"
  value       = module.bootstrap.terraform_state_bucket_name
}

output "terraform_state_bucket_url" {
  description = "URL of the Terraform state bucket"
  value       = module.bootstrap.terraform_state_bucket_url
}

output "project_id" {
  description = "The project ID where resources were created"
  value       = module.bootstrap.project_id
}

output "project_number" {
  description = "The project number"
  value       = module.bootstrap.project_number
}