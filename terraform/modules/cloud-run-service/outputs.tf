output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service."
  value       = google_cloud_run_service.backend.status[0].url
}

output "cloud_run_service_name" {
  description = "The name of the deployed Cloud Run service."
  value       = google_cloud_run_service.backend.name
}

output "region" {
  description = "The region where the Cloud Run service is deployed."
  value       = google_cloud_run_service.backend.location
}
