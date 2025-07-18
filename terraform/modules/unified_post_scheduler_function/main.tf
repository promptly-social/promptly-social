resource "google_storage_bucket_object" "unified_post_scheduler_source" {
  name   = "unified-post-scheduler-${var.source_hash}.zip"
  bucket = var.source_bucket
  source = data.archive_file.unified_post_scheduler_source.output_path
}

data "archive_file" "unified_post_scheduler_source" {
  type        = "zip"
  source_dir  = "${path.module}/../../src/gcp-functions"
  output_path = "/tmp/unified-post-scheduler-${var.source_hash}.zip"
  excludes = [
    "terraform/**",
    "README.md",
    "env.example",
    "test**",
    "test-output.json",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "htmlcov/**",
    "analyze/**",
    "generate-suggestions/**",
    "unified-post-scheduler/venv/**",
    "unified-post-scheduler/__pycache__/**",
    "unified-post-scheduler/.pytest_cache/**",
    "unified-post-scheduler/htmlcov/**",
    "unified-post-scheduler/test**"
  ]
}

resource "google_cloudfunctions2_function" "unified_post_scheduler" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "Unified post scheduler that processes scheduled posts every 5 minutes"

  build_config {
    runtime     = "python311"
    entry_point = "process_scheduled_posts"
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.unified_post_scheduler_source.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "512Mi"
    timeout_seconds    = 540  # 9 minutes to handle high loads
    
    environment_variables = {
      LINKEDIN_TOKEN_REFRESH_THRESHOLD = "60"
      MAX_RETRY_ATTEMPTS              = "3"
    }

    secret_environment_variables {
      key        = "SUPABASE_URL"
      project_id = var.project_id
      secret     = "SUPABASE_URL"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "SUPABASE_SERVICE_KEY"
      project_id = var.project_id
      secret     = "SUPABASE_SERVICE_KEY"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LINKEDIN_CLIENT_ID"
      project_id = var.project_id
      secret     = "LINKEDIN_CLIENT_ID"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LINKEDIN_CLIENT_SECRET"
      project_id = var.project_id
      secret     = "LINKEDIN_CLIENT_SECRET"
      version    = "latest"
    }

    ingress_settings = "ALLOW_INTERNAL_ONLY"
    
    service_account_email = var.service_account_email
  }

  depends_on = [
    google_storage_bucket_object.unified_post_scheduler_source,
    google_secret_manager_secret_iam_member.secret_access_supabase_url,
    google_secret_manager_secret_iam_member.secret_access_supabase_key,
    google_secret_manager_secret_iam_member.secret_access_linkedin_client_id,
    google_secret_manager_secret_iam_member.secret_access_linkedin_client_secret,
  ]
}

# Cloud Scheduler job to trigger the function every 5 minutes
resource "google_cloud_scheduler_job" "unified_post_scheduler" {
  project          = var.project_id
  region           = var.region
  name             = var.scheduler_job_name
  description      = "Triggers unified post scheduler every 5 minutes"
  schedule         = "*/5 * * * *"  # Every 5 minutes
  time_zone        = "UTC"
  attempt_deadline = "540s"  # 9 minutes

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.unified_post_scheduler.service_config[0].uri
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({}))  # Empty body since no parameters needed

    oidc_token {
      service_account_email = var.service_account_email
    }
  }

  depends_on = [
    google_cloudfunctions2_function.unified_post_scheduler
  ]
}

# IAM binding to allow Cloud Scheduler to invoke the function
resource "google_cloudfunctions2_function_iam_binding" "unified_post_scheduler_invoker" {
  project        = google_cloudfunctions2_function.unified_post_scheduler.project
  location       = google_cloudfunctions2_function.unified_post_scheduler.location
  cloud_function = google_cloudfunctions2_function.unified_post_scheduler.name
  role           = "roles/cloudfunctions.invoker"
  members = [
    "serviceAccount:${var.service_account_email}"
  ]
}

# Data sources for existing secrets
data "google_secret_manager_secret" "supabase_url" {
  project   = var.project_id
  secret_id = "SUPABASE_URL"
}

data "google_secret_manager_secret" "supabase_service_key" {
  project   = var.project_id
  secret_id = "SUPABASE_SERVICE_KEY"
}

data "google_secret_manager_secret" "linkedin_client_id" {
  project   = var.project_id
  secret_id = "LINKEDIN_CLIENT_ID"
}

data "google_secret_manager_secret" "linkedin_client_secret" {
  project   = var.project_id
  secret_id = "LINKEDIN_CLIENT_SECRET"
}

# Grant the function's service account access to the secrets
resource "google_secret_manager_secret_iam_member" "secret_access_supabase_url" {
  project   = data.google_secret_manager_secret.supabase_url.project
  secret_id = data.google_secret_manager_secret.supabase_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_supabase_key" {
  project   = data.google_secret_manager_secret.supabase_service_key.project
  secret_id = data.google_secret_manager_secret.supabase_service_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_linkedin_client_id" {
  project   = data.google_secret_manager_secret.linkedin_client_id.project
  secret_id = data.google_secret_manager_secret.linkedin_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_linkedin_client_secret" {
  project   = data.google_secret_manager_secret.linkedin_client_secret.project
  secret_id = data.google_secret_manager_secret.linkedin_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}