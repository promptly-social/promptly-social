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
    "roles/iam.serviceAccountUser",
    "roles/compute.loadBalancerAdmin"
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
  api_domain_name            = local.api_domain
  allow_unauthenticated_invocations = var.allow_unauthenticated_invocations
}

# --- Frontend Infrastructure (GCS Bucket + CDN for Static Site) ---

locals {
  frontend_domain = var.frontend_domain_name
  api_domain      = var.api_domain_name

  # Process the DNS records from the Cloud Run module
  api_dns_records = {
    for record in module.cloud_run_service[0].dns_records_for_custom_api_domain :
    # Create a unique key for each record to avoid collisions
    "${record.name}-${record.type}" => {
      name    = record.name
      type    = record.type
      rrdatas = [record.rrdata] # Wrap rrdata in a list
    } if var.manage_cloud_run_service && length(module.cloud_run_service) > 0 && module.cloud_run_service[0].dns_records_for_custom_api_domain != null
  }
}

# 1. Cloud Storage bucket to host static files
resource "google_storage_bucket" "frontend_bucket" {
  count = var.manage_frontend_infra ? 1 : 0

  name          = local.frontend_domain # Bucket names must be globally unique
  project       = var.project_id
  location      = "US"                  # Multi-regional for high availability
  storage_class = "STANDARD"

  # Consider setting to false in production to prevent accidental deletion
  # of the bucket and its contents.
  force_destroy = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html" # For SPAs, route all 404s to index.html
  }

  uniform_bucket_level_access = true

  depends_on = [google_project_service.apis]
}

# 2. Make all objects in the bucket publicly readable.
# This is required for the public-facing website served via the Load Balancer/CDN.
# With uniform_bucket_level_access enabled, this is the correct way to grant public access.
resource "google_storage_bucket_iam_member" "public_reader" {
  count = var.manage_frontend_infra ? 1 : 0

  bucket = google_storage_bucket.frontend_bucket[0].name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}


# 3. Reserve a static IP for the load balancer
resource "google_compute_global_address" "frontend_ip" {
  count = var.manage_frontend_infra ? 1 : 0

  name    = "${var.app_name}-frontend-ip-${var.environment}"
  project = var.project_id
}

# 4. Managed SSL Certificate for the custom domain
resource "google_compute_managed_ssl_certificate" "frontend_ssl" {
  count = var.manage_frontend_infra ? 1 : 0

  name = "${var.app_name}-frontend-ssl-${var.environment}"
  managed {
    domains = [local.frontend_domain]
  }
}

# 5. Backend bucket for the CDN
resource "google_compute_backend_bucket" "frontend_backend" {
  count = var.manage_frontend_infra ? 1 : 0

  name        = "${var.app_name}-frontend-backend-${var.environment}"
  project     = var.project_id
  bucket_name = google_storage_bucket.frontend_bucket[0].name
  enable_cdn  = true
  cdn_policy {
    # Cache static assets for 1 day.
    default_ttl          = 86400
    client_ttl           = 86400
    max_ttl              = 31536000 # 1 year
    cache_mode           = "CACHE_ALL_STATIC"
    negative_caching     = true
    signed_url_cache_max_age_sec = 0
  }
}

# 6. URL Map to route all requests to the backend bucket
resource "google_compute_url_map" "frontend_url_map" {
  count = var.manage_frontend_infra ? 1 : 0

  name            = "${var.app_name}-frontend-url-map-${var.environment}"
  project         = var.project_id
  default_service = google_compute_backend_bucket.frontend_backend[0].id
}

# 7. HTTPS Target Proxy
resource "google_compute_target_https_proxy" "frontend_https_proxy" {
  count = var.manage_frontend_infra ? 1 : 0

  name             = "${var.app_name}-frontend-https-proxy-${var.environment}"
  project          = var.project_id
  url_map          = google_compute_url_map.frontend_url_map[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.frontend_ssl[0].id]
}

# 8. Global Forwarding Rule (Load Balancer Frontend)
resource "google_compute_global_forwarding_rule" "frontend_forwarding_rule" {
  count = var.manage_frontend_infra ? 1 : 0

  name                  = "${var.app_name}-frontend-forwarding-rule-${var.environment}"
  project               = var.project_id
  target                = google_compute_target_https_proxy.frontend_https_proxy[0].id
  ip_address            = google_compute_global_address.frontend_ip[0].address
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# --- DNS for Frontend ---
# This creates a managed zone for 'promptly.social' and adds A records.
# NOTE: After running this, you must update the nameservers at your
# domain registrar to the ones provided in the `dns_zone_nameservers` output.
resource "google_dns_managed_zone" "frontend_zone" {
  count = var.manage_frontend_infra ? 1 : 0

  name     = "promptly-social-zone" # A name for the zone in GCP
  dns_name = "promptly.social."     # The actual domain name
  project  = var.project_id
  description = "DNS zone for promptly.social"
}

resource "google_dns_record_set" "frontend_a_record" {
  count = var.manage_frontend_infra ? 1 : 0

  managed_zone = google_dns_managed_zone.frontend_zone[0].name
  name         = "${local.frontend_domain}."
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.frontend_ip[0].address]
  project      = var.project_id
}

# Allow the app service account to write to the frontend bucket
resource "google_storage_bucket_iam_member" "frontend_bucket_writer" {
  count = var.manage_frontend_infra ? 1 : 0

  bucket = google_storage_bucket.frontend_bucket[0].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app_sa.email}"
}

# --- DNS for Backend API ---
# Create DNS records for the Cloud Run custom domain.
# It iterates over the record types (A, AAAA) returned by the Cloud Run module.
resource "google_dns_record_set" "api_records" {
  for_each = (var.manage_cloud_run_service && var.manage_frontend_infra) ? local.api_dns_records : {}

  managed_zone = google_dns_managed_zone.frontend_zone[0].name
  name         = "${each.value.name}."
  type         = each.value.type
  ttl          = 300
  rrdatas      = each.value.rrdatas
  project      = var.project_id
}