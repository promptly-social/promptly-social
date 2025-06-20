output "service_name" {
  description = "The name of the Cloud Run service."
  value       = google_cloud_run_service.backend.name
}

output "service_location" {
  description = "The location of the Cloud Run service."
  value       = google_cloud_run_service.backend.location
}
