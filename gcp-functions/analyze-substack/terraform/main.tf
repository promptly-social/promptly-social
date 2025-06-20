terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Data source for zipping the function code
data "archive_file" "source" {
  type        = "zip"
  source_dir  = ".."
  output_path = "/tmp/${var.function_name}.zip"
  excludes = [
    "terraform/**",
    "README.md",
    "deploy.sh",
    "env.example",
    "test_analyzer_local.py",
    "test_db_transcation_local.py",
    "test-output.json",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "htmlcov/**"
  ]
}

# Storage bucket to hold the zipped code
resource "google_storage_bucket" "source_bucket" {
  name          = "${var.app_name}-cf-source-${var.environment}"
  location      = var.region
  force_destroy = true # Set to false in production
  uniform_bucket_level_access = true
}

# Upload the zipped code to the bucket
resource "google_storage_bucket_object" "source_archive" {
  name   = "source.zip#${data.archive_file.source.output_md5}"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.source.output_path
}

# Service account for the Cloud Function
resource "google_service_account" "function_sa" {
  account_id   = "${var.function_name}-sa-${var.environment}"
  display_name = "Service Account for ${var.function_name} function"
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name     = var.function_name
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "analyze_substack"
    source {
      storage_source {
        bucket = google_storage_bucket.source_bucket.name
        object = google_storage_bucket_object.source_archive.name
      }
    }
  }

  service_config {
    max_instance_count             = 10
    available_memory               = "512MiB"
    timeout_seconds                = 600
    service_account_email          = google_service_account.function_sa.email
    all_traffic_on_latest_revision = true
    ingress_settings               = "ALLOW_ALL"

    environment_variables = {
      MAX_POSTS_TO_ANALYZE = var.max_posts_to_analyze
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
      key        = "OPENROUTER_API_KEY"
      project_id = var.project_id
      secret     = "OPENROUTER_API_KEY"
      version    = "latest"
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.secret_access_supabase_url,
    google_secret_manager_secret_iam_member.secret_access_supabase_key,
    google_secret_manager_secret_iam_member.secret_access_openrouter_key
  ]
}

# IAM policy to allow unauthenticated invocations
resource "google_cloud_run_service_iam_member" "invoker" {
  location = google_cloudfunctions2_function.function.location
  project  = google_cloudfunctions2_function.function.project
  service  = google_cloudfunctions2_function.function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Data sources for existing secrets
data "google_secret_manager_secret" "supabase_url" {
  secret_id = "SUPABASE_URL"
}

data "google_secret_manager_secret" "supabase_service_key" {
  secret_id = "SUPABASE_SERVICE_KEY"
}

data "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "OPENROUTER_API_KEY"
}

# Grant the function's service account access to the secrets
resource "google_secret_manager_secret_iam_member" "secret_access_supabase_url" {
  project   = data.google_secret_manager_secret.supabase_url.project
  secret_id = data.google_secret_manager_secret.supabase_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_supabase_key" {
  project   = data.google_secret_manager_secret.supabase_service_key.project
  secret_id = data.google_secret_manager_secret.supabase_service_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.function_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_openrouter_key" {
  project   = data.google_secret_manager_secret.openrouter_api_key.project
  secret_id = data.google_secret_manager_secret.openrouter_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.function_sa.email}"
} 