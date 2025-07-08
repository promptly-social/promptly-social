# Staging Environment Outputs

# Infrastructure module outputs
output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = module.infrastructure.cloud_run_service_name
}

output "api_load_balancer_ip" {
  description = "IP address of the API load balancer"
  value       = module.infrastructure.api_load_balancer_ip
}

output "api_url" {
  description = "The URL of the backend API"
  value       = module.infrastructure.api_url
}

output "artifact_registry_repository" {
  description = "Full name of the Artifact Registry repository"
  value       = module.infrastructure.artifact_registry_repository
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = module.infrastructure.artifact_registry_url
}

output "app_service_account_email" {
  description = "The email address of the service account created for the application"
  value       = module.infrastructure.app_service_account_email
}
