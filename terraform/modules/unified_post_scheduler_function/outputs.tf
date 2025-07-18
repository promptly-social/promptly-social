output "function_name" {
  description = "Name of the unified post scheduler function"
  value       = google_cloudfunctions2_function.unified_post_scheduler.name
}

output "function_uri" {
  description = "URI of the unified post scheduler function"
  value       = google_cloudfunctions2_function.unified_post_scheduler.service_config[0].uri
}

output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.unified_post_scheduler.name
}

output "function_id" {
  description = "Full resource ID of the function"
  value       = google_cloudfunctions2_function.unified_post_scheduler.id
}