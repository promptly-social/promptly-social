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
    "generate_suggestions/**",
    "unified_post_scheduler/venv/**",
    "unified_post_scheduler/__pycache__/**",
    "unified_post_scheduler/.pytest_cache/**",
    "unified_post_scheduler/htmlcov/**",
    "unified_post_scheduler/test**"
  ]
}

resource "google_cloudfunctions2_function" "unified_post_scheduler" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "Unified post scheduler that processes scheduled posts every 5 minutes"

  build_config {
    runtime     = "python313"
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
      key        = "POST_MEDIA_BUCKET_NAME"
      project_id = var.project_id
      secret     = "POST_MEDIA_BUCKET_NAME"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
      project_id = var.project_id
      secret     = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_DATABASE_NAME"
      project_id = var.project_id
      secret     = "CLOUD_SQL_DATABASE_NAME"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_USER"
      project_id = var.project_id
      secret     = "CLOUD_SQL_USER"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_PASSWORD"
      project_id = var.project_id
      secret     = "CLOUD_SQL_PASSWORD"
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
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_instance_connection_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_database_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_user,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_password,
    google_secret_manager_secret_iam_member.secret_access_linkedin_client_id,
    google_secret_manager_secret_iam_member.secret_access_linkedin_client_secret,
    google_secret_manager_secret_iam_member.secret_access_post_media_bucket_name,
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
data "google_secret_manager_secret" "cloud_sql_instance_connection_name" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
}

data "google_secret_manager_secret" "cloud_sql_database_name" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_DATABASE_NAME"
}

data "google_secret_manager_secret" "cloud_sql_user" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_USER"
}

data "google_secret_manager_secret" "cloud_sql_password" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_PASSWORD"
}

data "google_secret_manager_secret" "linkedin_client_id" {
  project   = var.project_id
  secret_id = "LINKEDIN_CLIENT_ID"
}

data "google_secret_manager_secret" "linkedin_client_secret" {
  project   = var.project_id
  secret_id = "LINKEDIN_CLIENT_SECRET"
}

data "google_secret_manager_secret" "post_media_bucket_name" {
  project   = var.project_id
  secret_id = "POST_MEDIA_BUCKET_NAME"
}

# Grant the function's service account access to the secrets
resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_instance_connection_name" {
  project   = data.google_secret_manager_secret.cloud_sql_instance_connection_name.project
  secret_id = data.google_secret_manager_secret.cloud_sql_instance_connection_name.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_database_name" {
  project   = data.google_secret_manager_secret.cloud_sql_database_name.project
  secret_id = data.google_secret_manager_secret.cloud_sql_database_name.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_user" {
  project   = data.google_secret_manager_secret.cloud_sql_user.project
  secret_id = data.google_secret_manager_secret.cloud_sql_user.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_password" {
  project   = data.google_secret_manager_secret.cloud_sql_password.project
  secret_id = data.google_secret_manager_secret.cloud_sql_password.secret_id
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

resource "google_secret_manager_secret_iam_member" "secret_access_post_media_bucket_name" {
  project   = data.google_secret_manager_secret.post_media_bucket_name.project
  secret_id = data.google_secret_manager_secret.post_media_bucket_name.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}