output "function_name" {
  description = "The name of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.name
}

output "function_url" {
  description = "The URL of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.service_config[0].uri
}

output "function_service_account_email" {
  description = "The email of the service account used by the Cloud Function"
  value       = google_service_account.function_sa.email
}

output "function_id" {
  description = "The ID of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.id
}