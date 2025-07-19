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
resource "google_storage_bucket_object" "analyze_source" {
  name   = "analyze-${var.source_hash}.zip"
  bucket = var.source_bucket
  source = data.archive_file.analyze_source.output_path
}

# Archive the function source code
data "archive_file" "analyze_source" {
  type        = "zip"
  source_dir  = var.function_source_dir
  output_path = "/tmp/analyze-${var.source_hash}.zip"
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
    "generate_suggestions/**",
    "unified_post_scheduler/**",
    "analyze/venv/**",
    "analyze/__pycache__/**",
    "analyze/.pytest_cache/**",
    "analyze/htmlcov/**",
    "analyze/test**"
  ]
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "Analyze function for content analysis"

  build_config {
    runtime     = "python313"
    entry_point = "analyze"
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.analyze_source.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "512Mi"
    timeout_seconds    = 600
    
    environment_variables = {
      MAX_POSTS_TO_ANALYZE = var.max_posts_to_analyze
      MAX_POSTS_TO_ANALYZE_LINKEDIN = var.max_posts_to_analyze_linkedin
      OPENROUTER_MODEL_PRIMARY = var.openrouter_model_primary
      OPENROUTER_MODELS_FALLBACK = join(",", var.openrouter_models_fallback)
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

    secret_environment_variables {
      key        = "APIFY_API_KEY"
      project_id = var.project_id
      secret     = "APIFY_API_KEY"
      version    = "latest"
    }

    ingress_settings = "ALLOW_ALL"
    
    service_account_email = var.service_account_email
  }

  depends_on = [
    google_storage_bucket_object.analyze_source,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_instance_connection_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_database_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_user,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_password,
    google_secret_manager_secret_iam_member.secret_access_openrouter_key,
    google_secret_manager_secret_iam_member.secret_access_apify_key,
    google_secret_manager_secret_iam_member.secret_access_gcp_function_url,
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

data "google_secret_manager_secret" "apify_api_key" {
  project   = var.project_id
  secret_id = "APIFY_API_KEY"
}

data "google_secret_manager_secret" "gcp_analysis_function_url" {
  project   = var.project_id
  secret_id = "GCP_ANALYSIS_FUNCTION_URL"
}

# Save the Cloud Function URL to Secret Manager
resource "google_secret_manager_secret_version" "gcp_analysis_function_url_version" {
  secret      = data.google_secret_manager_secret.gcp_analysis_function_url.id
  secret_data = google_cloudfunctions2_function.function.service_config[0].uri

  depends_on = [
    google_cloudfunctions2_function.function,
    google_secret_manager_secret_iam_member.secret_access_gcp_function_url
  ]
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

resource "google_secret_manager_secret_iam_member" "secret_access_apify_key" {
  project   = data.google_secret_manager_secret.apify_api_key.project
  secret_id = data.google_secret_manager_secret.apify_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_gcp_function_url" {
  project   = data.google_secret_manager_secret.gcp_analysis_function_url.project
  secret_id = data.google_secret_manager_secret.gcp_analysis_function_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}
