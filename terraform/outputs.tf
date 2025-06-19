output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.backend.name
}

# CloudSQL outputs removed - using Supabase

output "artifact_registry_repository" {
  description = "Full name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.backend_repo.name
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.docker_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}"
}

output "app_service_account_email" {
  description = "Email of the Application service account used by Cloud Run."
  value       = google_service_account.app_sa.email
}

output "secret_manager_secrets" {
  description = "List of Secret Manager secret IDs"
  value = [
    google_secret_manager_secret.jwt_secret.secret_id,
    google_secret_manager_secret.supabase_url.secret_id,
    google_secret_manager_secret.supabase_key.secret_id,
    google_secret_manager_secret.supabase_service_key.secret_id,
    google_secret_manager_secret.google_client_id.secret_id,
    google_secret_manager_secret.google_client_secret.secret_id,
    google_secret_manager_secret.gcp_analysis_function_url.secret_id
  ]
}

output "dns_records_for_custom_api_domain" {
  description = "The DNS records you must create at your domain registrar to point your custom API domain to the Cloud Run service."
  value       = google_cloud_run_domain_mapping.api_domain_mapping.status[0].resource_records
} 