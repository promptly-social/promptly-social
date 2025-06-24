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

resource "google_project_service" "project_services" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "logging.googleapis.com",
    "storage-component.googleapis.com",
  ])
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = false
  disable_dependent_services = false
}

# Data source for zipping the function code
data "archive_file" "source" {
  type        = "zip"
  source_dir  = var.function_source_dir
  output_path = "/tmp/${var.function_name}.zip"
  excludes = [
    "terraform/**",
    "README.md",
    "env.example",
    "test_posts_fetcher_local.py",
    "test_posts_generator_local.py",
    "filtered_posts.json",
    "generated_posts_*.json",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "htmlcov/**"
  ]
}

# Local variables for resource names
locals {
  bucket_name = "${var.app_name}-cf-source-${var.environment}"
  terraform_sa_email = "${var.app_name}-tf-sa-${var.environment}@${var.project_id}.iam.gserviceaccount.com"
}

# Storage bucket to hold the zipped code (reuse existing bucket from analyze-substack)
data "google_storage_bucket" "source_bucket" {
  name = local.bucket_name
}

# Upload the zipped code to the bucket
resource "google_storage_bucket_object" "source_archive" {
  name   = "generate-suggestions-source.zip#${data.archive_file.source.output_md5}"
  bucket = local.bucket_name
  source = data.archive_file.source.output_path

  # Make Terraform notice when the ZIP changes
  detect_md5hash = data.archive_file.source.output_md5
}

# Service account for the Cloud Function
resource "google_service_account" "function_sa" {
  account_id   = "${var.function_name}-sa-${var.environment}"
  display_name = "Service Account for ${var.function_name} function"

  depends_on = [google_project_service.project_services]

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      # Ignore changes to display_name if service account already exists
      display_name
    ]
  }
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name     = var.function_name
  location = var.region

  build_config {
    runtime     = "python313"
    entry_point = "generate_suggestions"
    source {
      storage_source {
        bucket = data.google_storage_bucket.source_bucket.name
        object = google_storage_bucket_object.source_archive.name
      }
    }
  }

  service_config {
    max_instance_count             = 10
    available_memory               = "512Mi"
    timeout_seconds                = 600
    service_account_email          = google_service_account.function_sa.email
    all_traffic_on_latest_revision = true
    ingress_settings               = "ALLOW_ALL"

    environment_variables = {
      NUMBER_OF_POSTS_TO_GENERATE = var.number_of_posts_to_generate
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
    google_secret_manager_secret_iam_member.secret_access_openrouter_key,
    google_project_iam_member.cloudbuild_storage_admin,
    google_project_iam_member.cloudbuild_functions_developer,
    google_project_iam_member.cloudbuild_run_admin,
    google_service_account_iam_member.cloudbuild_impersonate_function_sa,
    google_service_account_iam_member.cloudbuild_agent_impersonate_function_sa,
    google_project_iam_member.cloudbuild_logging_writer,
    google_project_iam_member.cloudbuild_artifactregistry_admin,
    google_project_iam_member.cloudbuild_service_account_token_creator,
    google_project_iam_member.compute_sa_logging_writer,
    google_project_iam_member.compute_sa_storage_viewer,
    google_project_iam_member.compute_sa_artifactregistry_writer,
    google_project_iam_member.compute_sa_token_creator,
    google_project_iam_member.function_sa_logging_writer,
    google_service_account_iam_member.functions_sa_impersonate_function_sa
  ]

  lifecycle {
    replace_triggered_by = [
      google_storage_bucket_object.source_archive
    ]
  }
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

# Data source for the GCP generate suggestions function URL secret
data "google_secret_manager_secret" "gcp_generate_suggestions_function_url" {
  secret_id = "GCP_GENERATE_SUGGESTIONS_FUNCTION_URL"
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

# Grant the function's service account permission to write to the GCP generate suggestions function URL secret
resource "google_secret_manager_secret_iam_member" "secret_access_gcp_function_url" {
  project   = data.google_secret_manager_secret.gcp_generate_suggestions_function_url.project
  secret_id = data.google_secret_manager_secret.gcp_generate_suggestions_function_url.secret_id
  role      = "roles/secretmanager.secretVersionManager"
  member    = "serviceAccount:${google_service_account.function_sa.email}"
}

# Grant the function's service account permission to write logs
resource "google_project_iam_member" "function_sa_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

# Data source to get project number for Cloud Build service account
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_project_service_identity" "gcp_sa_cloudfunctions" {
  provider = google-beta
  project  = var.project_id
  service  = "cloudfunctions.googleapis.com"

  depends_on = [
    google_project_service.project_services,
  ]
}

# Grant Cloud Build service account necessary permissions for building Cloud Functions
resource "google_project_iam_member" "cloudbuild_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_functions_developer" {
  project = var.project_id
  role    = "roles/cloudfunctions.developer"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Grant Cloud Build SA permission to impersonate the function's runtime SA
resource "google_service_account_iam_member" "cloudbuild_impersonate_function_sa" {
  service_account_id = google_service_account.function_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Grant the Terraform SA permission to impersonate the function's runtime SA
resource "google_service_account_iam_member" "terraform_sa_impersonate_function_sa" {
  service_account_id = google_service_account.function_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.terraform_sa_email}"
}

# Grant Cloud Build Service Agent permission to impersonate the function's runtime SA
resource "google_service_account_iam_member" "cloudbuild_agent_impersonate_function_sa" {
  service_account_id = google_service_account.function_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

# Grant the Cloud Functions Service Agent permission to act as the function's runtime SA.
# This is necessary for the service to manage the function.
resource "google_service_account_iam_member" "functions_sa_impersonate_function_sa" {
  service_account_id = google_service_account.function_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_project_service_identity.gcp_sa_cloudfunctions.email}"
}

# Grant the Cloud Build service account permission to write logs
resource "google_project_iam_member" "cloudbuild_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_artifactregistry_admin" {
  project = var.project_id
  role    = "roles/artifactregistry.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_service_account_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Grant the Compute Engine default SA permission to write logs, as required by the build process.
resource "google_project_iam_member" "compute_sa_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant the Compute Engine default SA permission to read GCS objects for the build process.
resource "google_project_iam_member" "compute_sa_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant the Compute Engine default SA permission to download artifacts from Artifact Registry.
resource "google_project_iam_member" "compute_sa_artifactregistry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant the Compute Engine default SA the ability to create tokens for other services.
resource "google_project_iam_member" "compute_sa_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
} 