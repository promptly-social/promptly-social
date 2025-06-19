terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
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
    "iam.googleapis.com"
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
    "roles/cloudtrace.agent"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_sa.email}"
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
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
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

# Grant Secret Manager access to the service account
resource "google_secret_manager_secret_iam_member" "secrets_access" {
  for_each = toset([
    google_secret_manager_secret.jwt_secret.secret_id,
    google_secret_manager_secret.supabase_url.secret_id,
    google_secret_manager_secret.supabase_key.secret_id,
    google_secret_manager_secret.supabase_service_key.secret_id,
    google_secret_manager_secret.google_client_id.secret_id,
    google_secret_manager_secret.google_client_secret.secret_id,
    google_secret_manager_secret.gcp_analysis_function_url.secret_id
  ])

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_sa.email}"
}

# Cloud Run service
# resource "google_cloud_run_service" "backend" {
#   name     = "${var.app_name}-backend-${var.environment}"
#   location = var.region
# 
#   template {
#     metadata {
#       annotations = {
#         "autoscaling.knative.dev/minScale"         = var.cloud_run_min_instances
#         "autoscaling.knative.dev/maxScale"         = var.cloud_run_max_instances
#         "run.googleapis.com/execution-environment" = "gen2"
#       }
#     }
# 
#     spec {
#       service_account_name = google_service_account.app_sa.email
# 
#       containers {
#         image = "${var.docker_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/backend:latest"
# 
#         ports {
#           container_port = 8000
#         }
# 
#         resources {
#           limits = {
#             cpu    = var.cloud_run_cpu
#             memory = var.cloud_run_memory
#           }
#         }
# 
#         env {
#           name  = "ENVIRONMENT"
#           value = var.environment
#         }
# 
#         # PORT is set automatically by Cloud Run
#         # env {
#         #   name  = "PORT"
#         #   value = "8000"
#         # }
# 
#         env {
#           name  = "CORS_ORIGINS"
#           value = join(",", var.cors_origins)
#         }
# 
#         # DATABASE_URL removed - using Supabase
# 
#         env {
#           name = "JWT_SECRET_KEY"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.jwt_secret.secret_id
#               key  = "latest"
#             }
#           }
#         }
# 
#         env {
#           name = "SUPABASE_URL"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.supabase_url.secret_id
#               key  = "latest"
#             }
#           }
#         }
# 
#         env {
#           name = "SUPABASE_KEY"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.supabase_key.secret_id
#               key  = "latest"
#             }
#           }
#         }
# 
#         env {
#           name = "SUPABASE_SERVICE_KEY"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.supabase_service_key.secret_id
#               key  = "latest"
#             }
#           }
#         }
# 
#         env {
#           name = "GOOGLE_CLIENT_ID"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.google_client_id.secret_id
#               key  = "latest"
#             }
#           }
#         }
# 
#         env {
#           name = "GOOGLE_CLIENT_SECRET"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.google_client_secret.secret_id
#               key  = "latest"
#             }
#           }
#         }
# 
#         env {
#           name = "GCP_ANALYSIS_FUNCTION_URL"
#           value_from {
#             secret_key_ref {
#               name = google_secret_manager_secret.gcp_analysis_function_url.secret_id
#               key  = "latest"
#             }
#           }
#         }
#       }
#     }
#   }
# 
#   traffic {
#     percent         = 100
#     latest_revision = true
#   }
# 
#   depends_on = [google_project_service.apis, google_artifact_registry_repository.backend_repo]
# }

# Allow public access to Cloud Run service
# resource "google_cloud_run_service_iam_member" "public_access" {
#   service  = google_cloud_run_service.backend.name
#   location = google_cloud_run_service.backend.location
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }

# Map the custom domain to the Cloud Run service
# resource "google_cloud_run_domain_mapping" "api_domain_mapping" {
#   location = google_cloud_run_service.backend.location
#   name     = var.api_domain_name
# 
#   metadata {
#     namespace = var.project_id
#   }
# 
#   spec {
#     route_name = google_cloud_run_service.backend.name
#   }
# } 