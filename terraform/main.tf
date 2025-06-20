terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
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
  zone    = var.zone
}

data "google_project" "current" {}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com"
  ])

  service            = each.value
  disable_on_destroy = false
}

# Create Artifact Registry for Docker images
resource "google_artifact_registry_repository" "backend_repo" {
  repository_id = "${var.app_name}-backend"
  location      = var.docker_registry_location
  format        = "DOCKER"
  description   = "Docker repository for ${var.app_name} backend"

  depends_on = [google_project_service.apis]
}


# Service account for Cloud Run
resource "google_service_account" "app_sa" {
  account_id   = "${var.app_name}-app-sa-${var.environment}"
  display_name = "App Service Account for ${var.app_name} (${var.environment})"
  description  = "Service account for the main application, used by Cloud Run."
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "cloud_run_permissions" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/run.admin",
    "roles/iam.serviceAccountUser"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

# Allow the service account to push to the Artifact Registry repository
resource "google_artifact_registry_repository_iam_member" "writer" {
  location   = google_artifact_registry_repository.backend_repo.location
  repository = google_artifact_registry_repository.backend_repo.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.app_sa.email}"
}

# Workload Identity Federation for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "${var.app_name}-github-pool"
  display_name              = "${var.app_name} GitHub Actions Pool"
  description               = "Workload Identity Pool for GitHub Actions CI/CD"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"
  description                        = "OIDC provider for GitHub Actions"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  attribute_condition = "assertion.repository_owner == 'promptly-social'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub Actions to impersonate the Application Service Account
resource "google_service_account_iam_binding" "app_sa_wif_binding" {
  service_account_id = google_service_account.app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    # Allow workflows from your GitHub repository to impersonate this SA
    "principalSet://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/attribute.repository/${var.github_repo}"
  ]

  depends_on = [
    google_iam_workload_identity_pool_provider.github_provider
  ]
}

# Secret Manager secrets

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "JWT_SECRET_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "SUPABASE_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_key" {
  secret_id = "SUPABASE_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_service_key" {
  secret_id = "SUPABASE_SERVICE_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "GOOGLE_CLIENT_ID"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "GOOGLE_CLIENT_SECRET"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gcp_analysis_function_url" {
  secret_id = "GCP_ANALYSIS_FUNCTION_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "OPENROUTER_API_KEY"

  replication {
    auto {}
  }
}

# Data source to get the current version of the GCP analysis function URL secret
data "google_secret_manager_secret_version" "gcp_analysis_function_url_version" {
  secret = google_secret_manager_secret.gcp_analysis_function_url.secret_id
}

# Null resource to trigger Cloud Run service restart when the function URL changes
resource "null_resource" "restart_cloud_run_on_function_url_change" {
  count = var.manage_cloud_run_service ? 1 : 0
  
  triggers = {
    function_url_version = data.google_secret_manager_secret_version.gcp_analysis_function_url_version.version
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud run services update ${var.app_name}-backend-${var.environment} \
        --region=${var.region} \
        --project=${var.project_id} \
        --update-env-vars=RESTART_TRIGGER=$(date +%s)
    EOT
  }

  depends_on = [module.cloud_run_service]
}

# Grant Secret Manager access to the service account
resource "google_secret_manager_secret_iam_member" "secrets_access" {
  for_each = {
    jwt_secret            = google_secret_manager_secret.jwt_secret
    supabase_url          = google_secret_manager_secret.supabase_url
    supabase_key          = google_secret_manager_secret.supabase_key
    supabase_service_key  = google_secret_manager_secret.supabase_service_key
    google_client_id      = google_secret_manager_secret.google_client_id
    google_client_secret  = google_secret_manager_secret.google_client_secret
    gcp_analysis_function_url = google_secret_manager_secret.gcp_analysis_function_url
    openrouter_api_key    = google_secret_manager_secret.openrouter_api_key
  }

  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_sa.email}"
}

module "cloud_run_service" {
  count  = var.manage_cloud_run_service ? 1 : 0
  source = "../../modules/cloud-run-service"

  project_id                 = var.project_id
  region                     = var.region
  app_name                   = var.app_name
  environment                = var.environment
  cloud_run_min_instances    = var.cloud_run_min_instances
  cloud_run_max_instances    = var.cloud_run_max_instances
  cloud_run_cpu              = var.cloud_run_cpu
  cloud_run_memory           = var.cloud_run_memory
  service_account_email      = google_service_account.app_sa.email
  docker_registry_location   = var.docker_registry_location
  backend_repo_repository_id = google_artifact_registry_repository.backend_repo.repository_id
  cors_origins               = var.cors_origins
  jwt_secret_name            = google_secret_manager_secret.jwt_secret.secret_id
  supabase_url_name          = google_secret_manager_secret.supabase_url.secret_id
  supabase_key_name          = google_secret_manager_secret.supabase_key.secret_id
  supabase_service_key_name  = google_secret_manager_secret.supabase_service_key.secret_id
  google_client_id_name      = google_secret_manager_secret.google_client_id.secret_id
  google_client_secret_name  = google_secret_manager_secret.google_client_secret.secret_id
  gcp_analysis_function_url_name = google_secret_manager_secret.gcp_analysis_function_url.secret_id
  openrouter_api_key_name    = google_secret_manager_secret.openrouter_api_key.secret_id
  api_domain_name            = var.api_domain_name
  allow_unauthenticated_invocations = var.allow_unauthenticated_invocations
}