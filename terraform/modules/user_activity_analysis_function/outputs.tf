output "function_uri" {
  description = "The URI of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.service_config[0].uri
}

output "function_name" {
  description = "The name of the deployed Cloud Function"
  value       = google_cloudfunctions2_function.function.name
}

output "scheduler_job_name" {
  description = "The name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.user_activity_analysis.name
}

output "scheduler_job_id" {
  description = "The ID of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.user_activity_analysis.id
}
