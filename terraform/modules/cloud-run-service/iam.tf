# Allow public access to the Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_unauthenticated_invocations ? 1 : 0

  location = google_cloud_run_service.backend.location
  service  = google_cloud_run_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_service.backend]
}
