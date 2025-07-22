terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Storage bucket object for function source code
resource "google_storage_bucket_object" "user_activity_analysis_source" {
  name   = "user-activity-analysis-${var.source_hash}.zip"
  bucket = var.source_bucket
  source = data.archive_file.user_activity_analysis_source.output_path
}

# Archive the function source code
data "archive_file" "user_activity_analysis_source" {
  type        = "zip"
  source_dir  = var.function_source_dir
  output_path = "/tmp/user-activity-analysis-${var.source_hash}.zip"
  excludes = [
    "terraform/**",
    "README.md",
    "env.example",
    ".env",
    "test**",
    "test-output.json",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "htmlcov/**",
    "analyze/**",
    "generate_suggestions/**",
    "unified_post_scheduler/**",
    "user_activity_analysis/venv/**",
    "user_activity_analysis/__pycache__/**",
    "user_activity_analysis/.pytest_cache/**",
    "user_activity_analysis/htmlcov/**",
    "user_activity_analysis/test**"
  ]
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "User activity analysis function that runs daily at midnight PDT to analyze user engagement patterns"

  build_config {
    runtime     = "python313"
    entry_point = "analyze_user_activity"
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.user_activity_analysis_source.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "1Gi"
    timeout_seconds    = 900  # 15 minutes as per requirements
    
    environment_variables = {
      POST_THRESHOLD               = var.post_threshold
      MESSAGE_THRESHOLD            = var.message_threshold
      MAX_RETRY_ATTEMPTS           = var.max_retry_attempts
      ANALYSIS_TIMEOUT_MINUTES     = var.analysis_timeout_minutes
      BATCH_SIZE                   = var.batch_size
      OPENROUTER_MODEL_PRIMARY     = var.openrouter_model_primary
      OPENROUTER_MODELS_FALLBACK   = join(",", var.openrouter_models_fallback)
      OPENROUTER_MODEL_TEMPERATURE = var.openrouter_model_temperature
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
      key        = "OPENROUTER_API_KEY"
      project_id = var.project_id
      secret     = "OPENROUTER_API_KEY"
      version    = "latest"
    }

    ingress_settings = "ALLOW_INTERNAL_ONLY"
    
    service_account_email = var.service_account_email
  }

  depends_on = [
    google_storage_bucket_object.user_activity_analysis_source,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_instance_connection_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_database_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_user,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_password,
    google_secret_manager_secret_iam_member.secret_access_openrouter_key,
  ]
}

# Cloud Scheduler job to trigger the function daily at midnight PDT
resource "google_cloud_scheduler_job" "user_activity_analysis" {
  project          = var.project_id
  region           = var.region
  name             = var.scheduler_job_name
  description      = "Triggers user activity analysis function daily at midnight PDT with comprehensive retry and monitoring"
  schedule         = var.schedule
  time_zone        = var.timezone
  attempt_deadline = "900s"  # 15 minutes as per requirements
  paused           = var.scheduler_paused

  retry_config {
    retry_count          = var.scheduler_retry_count
    max_retry_duration   = var.scheduler_max_retry_duration
    min_backoff_duration = var.scheduler_min_backoff_duration
    max_backoff_duration = var.scheduler_max_backoff_duration
    max_doublings        = var.scheduler_max_doublings
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.function.service_config[0].uri
    
    headers = {
      "Content-Type" = "application/json"
      "X-Scheduler-Job" = var.scheduler_job_name
      "X-Environment" = var.environment
    }
    
    # Include metadata in the request body for better tracking
    body = base64encode(jsonencode({
      scheduler_job_name = var.scheduler_job_name
      environment       = var.environment
      triggered_at      = "{{.ScheduleTime}}"
      attempt_number    = "{{.AttemptNumber}}"
    }))

    oidc_token {
      service_account_email = var.service_account_email
      audience             = google_cloudfunctions2_function.function.service_config[0].uri
    }
  }

  depends_on = [
    google_cloudfunctions2_function.function
  ]
}



# IAM binding to allow Cloud Scheduler to invoke the function
resource "google_cloudfunctions2_function_iam_binding" "user_activity_analysis_invoker" {
  project        = google_cloudfunctions2_function.function.project
  location       = google_cloudfunctions2_function.function.location
  cloud_function = google_cloudfunctions2_function.function.name
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

data "google_secret_manager_secret" "openrouter_api_key" {
  project   = var.project_id
  secret_id = "OPENROUTER_API_KEY"
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

resource "google_secret_manager_secret_iam_member" "secret_access_openrouter_key" {
  project   = data.google_secret_manager_secret.openrouter_api_key.project
  secret_id = data.google_secret_manager_secret.openrouter_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}