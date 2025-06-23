# Cloud Run service
resource "google_cloud_run_service" "backend" {
  name     = "${var.app_name}-backend-${var.environment}"
  location = var.region

  autogenerate_revision_name = false

  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "internal-and-cloud-load-balancing"
    }
  }

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"         = var.cloud_run_min_instances
        "autoscaling.knative.dev/maxScale"         = var.cloud_run_max_instances
        "run.googleapis.com/execution-environment" = "gen2"
        "terraform.io/last-applied" = timestamp()
      }
    }

    spec {
      service_account_name = var.service_account_email

      containers {
        image = "${var.docker_registry_location}-docker.pkg.dev/${var.project_id}/${var.backend_repo_repository_id}/backend:${var.image_tag}"

        ports {
          container_port = 8000
        }

        resources {
          limits = {
            cpu    = var.cloud_run_cpu
            memory = var.cloud_run_memory
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

      
        env {
          name  = "CORS_ORIGINS"
          value = join(",", var.cors_origins)
        }

        env {
          name = "JWT_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = var.jwt_secret_name
              key  = "latest"
            }
          }
        }

        env {
          name = "SUPABASE_URL"
          value_from {
            secret_key_ref {
              name = var.supabase_url_name
              key  = "latest"
            }
          }
        }

        env {
          name = "SUPABASE_KEY"
          value_from {
            secret_key_ref {
              name = var.supabase_key_name
              key  = "latest"
            }
          }
        }

        env {
          name = "SUPABASE_SERVICE_KEY"
          value_from {
            secret_key_ref {
              name = var.supabase_service_key_name
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = var.google_client_id_name
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = var.google_client_secret_name
              key  = "latest"
            }
          }
        }

        env {
          name = "GCP_ANALYSIS_FUNCTION_URL"
          value_from {
            secret_key_ref {
              name = var.gcp_analysis_function_url_name
              key  = "latest"
            }
          }
        }

        env {
          name = "OPENROUTER_API_KEY"
          value_from {
            secret_key_ref {
              name = var.openrouter_api_key_name
              key  = "latest"
            }
          }
        }

        env {
          name  = "GCP_ANALYSIS_FUNCTION_URL_VERSION"
          value = var.gcp_analysis_function_url_version
        }
        env {
          name  = "FRONTEND_URL"
          value = var.frontend_url
        }

        env {
          name  = "BACKEND_URL"
          value = var.backend_url
        }

        env {
          name = "LINKEDIN_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = var.linkedin_client_id_name
              key  = "latest"
            }
          }
        }

        env {
          name = "LINKEDIN_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = var.linkedin_client_secret_name
              key  = "latest"
            }
          }
        }

        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = var.database_url_name
              key  = "latest"
            }
          }
        }

        env {
          name = "UNIPILE_DSN"
          value_from {
            secret_key_ref {
              name = var.unipile_dsn_name
              key  = "latest"
            }
          }
        }

        env {
          name = "UNIPILE_ACCESS_TOKEN"
          value_from {
            secret_key_ref {
              name = var.unipile_access_token_name
              key  = "latest"
            }
          }
        }

        env {
          name = "USE_UNIPILE_FOR_LINKEDIN"
          value_from {
            secret_key_ref {
              name = var.use_unipile_for_linkedin_name
              key  = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
