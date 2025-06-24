output "function_uri" {
  description = "The URI of the deployed Cloud Function."
  value       = google_cloudfunctions2_function.function.service_config[0].uri
}

output "function_url_secret_version" {
  description = "The version of the secret containing the function URL."
  value       = google_secret_manager_secret_version.gcp_generate_suggestions_function_url_version.version
} 