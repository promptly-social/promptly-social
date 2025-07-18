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
resource "google_storage_bucket_object" "analyze_substack_source" {
  name   = "analyze-substack-${var.source_hash}.zip"
  bucket = var.source_bucket
  source = data.archive_file.analyze_substack_source.output_path
}

# Archive the function source code
data "archive_file" "analyze_substack_source" {
  type        = "zip"
  source_dir  = var.function_source_dir
  output_path = "/tmp/analyze-substack-${var.source_hash}.zip"
  excludes = [
    "terraform/**",
    "README.md",
    "env.example",
    "test**",
    "test-output.json",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "htmlcov/**"
  ]
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "Analyze substack function for content analysis"

  build_config {
    runtime     = "python313"
    entry_point = "analyze_substack"
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.analyze_substack_source.name
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
    google_storage_bucket_object.analyze_substack_source,
    google_secret_manager_secret_iam_member.secret_access_supabase_url,
    google_secret_manager_secret_iam_member.secret_access_supabase_key,
    google_secret_manager_secret_iam_member.secret_access_openrouter_key,
    google_secret_manager_secret_iam_member.secret_access_apify_key,
    google_secret_manager_secret_iam_member.secret_access_gcp_function_url,
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
