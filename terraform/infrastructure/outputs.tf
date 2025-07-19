output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "cloud_run_service_name" {
  description = "The name of the Cloud Run service."
  value       = var.manage_cloud_run_service && length(module.cloud_run_service) > 0 ? module.cloud_run_service[0].service_name : "n/a"
}

output "api_load_balancer_ip" {
  description = "The IP address of the backend API load balancer."
  value       = var.manage_cloud_run_service && length(google_compute_global_address.api_ip) > 0 ? google_compute_global_address.api_ip[0].address : "n/a"
}

output "api_url" {
  description = "The URL of the backend API."
  value       = "https://api.${var.frontend_domain_name}"
}

output "artifact_registry_repository" {
  description = "Full name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.backend_repo.name
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.docker_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}"
}

output "app_service_account_email" {
  description = "The email address of the service account created for the application."
  value       = data.google_service_account.app_sa.email
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
    google_secret_manager_secret.gcp_analysis_function_url.secret_id,
    google_secret_manager_secret.gcp_generate_suggestions_function_url.secret_id
  ]
}

output "frontend_bucket_name" {
  description = "Name of the GCS bucket for the frontend."
  value       = var.manage_frontend_infra ? google_storage_bucket.frontend_bucket[0].name : "n/a"
}

output "cf_source_bucket_name" {
  description = "Name of the GCS bucket for Cloud Function source code."
  value       = google_storage_bucket.cf_source_bucket.name
}

output "frontend_static_ip" {
  description = "Static IP for the frontend load balancer."
  value       = var.manage_frontend_infra ? google_compute_global_address.frontend_ip[0].address : "n/a"
}

output "frontend_domain" {
  description = "The domain name for the frontend"
  value       = var.manage_frontend_infra ? local.frontend_domain : "Not managed by this configuration."
}

output "dns_zone_nameservers" {
  description = "Nameservers for the Cloud DNS managed zone. Update these in your domain registrar."
  value       = var.manage_frontend_infra && local.is_production ? google_dns_managed_zone.frontend_zone[0].name_servers : ["DNS zone not managed by this configuration."]
}

output "dns_zone_name" {
  description = "The name of the DNS managed zone."
  value       = var.manage_frontend_infra && local.is_production ? google_dns_managed_zone.frontend_zone[0].name : "n/a"
}

# Cloud SQL Outputs
output "cloud_sql_instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = module.cloud_sql.instance_name
}

output "cloud_sql_instance_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = module.cloud_sql.instance_connection_name
}

output "cloud_sql_private_ip_address" {
  description = "The private IP address of the Cloud SQL instance"
  value       = module.cloud_sql.private_ip_address
}

output "cloud_sql_database_name" {
  description = "The name of the main database"
  value       = module.cloud_sql.database_name
}

output "cloud_sql_connection_info" {
  description = "Database connection information for applications"
  value       = module.cloud_sql.connection_info
  sensitive   = true
}

output "cloud_sql_secret_references" {
  description = "Secret Manager references for database credentials"
  value       = module.cloud_sql.secret_references
}