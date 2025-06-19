output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service."
  value       = google_cloud_run_service.backend.status[0].url
}

output "cloud_run_service_name" {
  description = "The name of the deployed Cloud Run service."
  value       = google_cloud_run_service.backend.name
}

output "dns_records_for_custom_api_domain" {
  description = "The DNS records needed to map the custom API domain to the Cloud Run service."
  value       = google_cloud_run_domain_mapping.api_domain_mapping.status[0].resource_records
}
