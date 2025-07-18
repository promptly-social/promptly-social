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
resource "google_storage_bucket_object" "generate_suggestions_source" {
  name   = "generate-suggestions-${var.source_hash}.zip"
  bucket = var.source_bucket
  source = data.archive_file.generate_suggestions_source.output_path
}

# Archive the function source code
data "archive_file" "generate_suggestions_source" {
  type        = "zip"
  source_dir  = var.function_source_dir
  output_path = "/tmp/generate-suggestions-${var.source_hash}.zip"
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "Generate suggestions function for social media posts"

  build_config {
    runtime     = "python313"
    entry_point = "generate_suggestions"
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.generate_suggestions_source.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "512Mi"
    timeout_seconds    = 600
    
    environment_variables = {
      NUMBER_OF_POSTS_TO_GENERATE = var.number_of_posts_to_generate
      OPENROUTER_MODEL_PRIMARY = var.openrouter_model_primary
      OPENROUTER_MODELS_FALLBACK = join(",", var.openrouter_models_fallback)
      OPENROUTER_MODEL_TEMPERATURE = var.openrouter_model_temperature
      OPENROUTER_LARGE_MODEL_PRIMARY = var.openrouter_large_model_primary
      OPENROUTER_LARGE_MODELS_FALLBACK = join(",", var.openrouter_large_models_fallback)
      OPENROUTER_LARGE_MODEL_TEMPERATURE = var.openrouter_large_model_temperature
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
      key        = "ZYTE_API_KEY"
      project_id = var.project_id
      secret     = "ZYTE_API_KEY"
      version    = "latest"
    }

    ingress_settings = "ALLOW_ALL"
    
    service_account_email = var.service_account_email
  }

  depends_on = [
    google_storage_bucket_object.generate_suggestions_source,
    google_secret_manager_secret_iam_member.secret_access_supabase_url,
    google_secret_manager_secret_iam_member.secret_access_supabase_key,
    google_secret_manager_secret_iam_member.secret_access_openrouter_key,
    google_secret_manager_secret_iam_member.secret_access_zyte_key,
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

data "google_secret_manager_secret" "zyte_api_key" {
  project   = var.project_id
  secret_id = "ZYTE_API_KEY"
}

data "google_secret_manager_secret" "gcp_generate_suggestions_function_url" {
  project   = var.project_id
  secret_id = "GCP_GENERATE_SUGGESTIONS_FUNCTION_URL"
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

resource "google_secret_manager_secret_iam_member" "secret_access_zyte_key" {
  project   = data.google_secret_manager_secret.zyte_api_key.project
  secret_id = data.google_secret_manager_secret.zyte_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_gcp_function_url" {
  project   = data.google_secret_manager_secret.gcp_generate_suggestions_function_url.project
  secret_id = data.google_secret_manager_secret.gcp_generate_suggestions_function_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}


# Save the Cloud Function URL to Secret Manager
resource "google_secret_manager_secret_version" "gcp_generate_suggestions_function_url_version" {
  secret      = data.google_secret_manager_secret.gcp_generate_suggestions_function_url.id
  secret_data = google_cloudfunctions2_function.function.service_config[0].uri

  depends_on = [
    google_cloudfunctions2_function.function,
    google_secret_manager_secret_iam_member.secret_access_gcp_function_url
  ]
}
