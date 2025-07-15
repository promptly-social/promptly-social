# terraform/infrastructure/main.tf
# This module manages application infrastructure, assuming bootstrap has created foundational resources

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
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9.1"
    }
  }
}

# Configure the default provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Configure the DNS provider for cross-project DNS management
provider "google" {
  alias   = "dns"
  project = local.is_production ? var.project_id : var.production_project_id
}

data "google_project" "current" {}

# Data source to get the production DNS managed zone when running for staging
data "google_dns_managed_zone" "production_zone" {
  count   = !local.is_production ? 1 : 0
  name    = "promptly-social-zone"
  project = var.production_project_id # This var should be set in staging's .tfvars
}

# Enable application-specific APIs (foundational APIs are enabled by bootstrap)
resource "google_project_service" "application_apis" {
  for_each = toset([
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "dns.googleapis.com",
    "cloudscheduler.googleapis.com"
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

  depends_on = [google_project_service.application_apis]
}

# Create Storage Bucket for post media
resource "google_storage_bucket" "post_media_bucket" {
  name          = "${var.app_name}-post-media-${var.environment}"
  project       = var.project_id
  location      = "US"
  storage_class = "STANDARD"

  force_destroy = true # Consider setting to false in production

  uniform_bucket_level_access = true

  cors {
    origin          = local.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["Content-Type", "Authorization", "x-goog-resumable"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.application_apis]
}

# Grant App SA access to the post media bucket
resource "google_storage_bucket_iam_member" "app_sa_post_media_bucket_admin" {
  bucket = google_storage_bucket.post_media_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${data.google_service_account.app_sa.email}"
}

# Reference service accounts created by bootstrap module
data "google_service_account" "app_sa" {
  account_id = "${var.app_name}-app-sa-${var.environment}"
  project    = var.project_id
}

# Grant Artifact Registry writer role to the application service account
resource "google_artifact_registry_repository_iam_member" "app_sa_artifact_registry_writer" {
  provider   = google
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.backend_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_service_account.app_sa.email}"
  
  # Explicitly depend on the repository being created first
  depends_on = [
    google_artifact_registry_repository.backend_repo,
    google_project_service.application_apis["artifactregistry.googleapis.com"]
  ]
  
  # Add a lifecycle block to handle cases where the repository might be created outside of Terraform
  lifecycle {
    ignore_changes = [
      # Ignore changes to the repository name in case it's managed elsewhere
      repository,
    ]
  }
}

data "google_service_account" "terraform_sa" {
  account_id = "${var.app_name}-tf-sa-${var.environment}"
  project    = var.project_id
}

# Grant application-specific permissions to the App SA
# (Bootstrap handles foundational permissions for Terraform SA)
resource "google_project_iam_member" "app_sa_runtime_permissions" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/run.developer",
    "roles/artifactregistry.reader",
    "roles/cloudscheduler.admin"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_service_account.app_sa.email}"
}

# Workload Identity Federation and service account impersonation are handled by the bootstrap module

# Secret Manager secrets

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "JWT_SECRET_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_initial_version" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "SUPABASE_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "supabase_url_initial_version" {
  secret      = google_secret_manager_secret.supabase_url.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "supabase_key" {
  secret_id = "SUPABASE_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "supabase_key_initial_version" {
  secret      = google_secret_manager_secret.supabase_key.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "supabase_service_key" {
  secret_id = "SUPABASE_SERVICE_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "supabase_service_key_initial_version" {
  secret      = google_secret_manager_secret.supabase_service_key.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "GOOGLE_CLIENT_ID"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "google_client_id_initial_version" {
  secret      = google_secret_manager_secret.google_client_id.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "GOOGLE_CLIENT_SECRET"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "google_client_secret_initial_version" {
  secret      = google_secret_manager_secret.google_client_secret.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "gcp_analysis_function_url" {
  secret_id = "GCP_ANALYSIS_FUNCTION_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gcp_analysis_function_url_initial_version" {
  secret      = google_secret_manager_secret.gcp_analysis_function_url.id
  secret_data = "https://placeholder.url/update-me"
}

resource "google_secret_manager_secret" "gcp_generate_suggestions_function_url" {
  secret_id = "GCP_GENERATE_SUGGESTIONS_FUNCTION_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gcp_generate_suggestions_function_url_initial_version" {
  secret      = google_secret_manager_secret.gcp_generate_suggestions_function_url.id
  secret_data = "https://placeholder.url/update-me"
}

resource "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "OPENROUTER_API_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_api_key_initial_version" {
  secret      = google_secret_manager_secret.openrouter_api_key.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "linkedin_client_id" {
  secret_id = "LINKEDIN_CLIENT_ID"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "linkedin_client_id_initial_version" {
  secret      = google_secret_manager_secret.linkedin_client_id.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "linkedin_client_secret" {
  secret_id = "LINKEDIN_CLIENT_SECRET"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "linkedin_client_secret_initial_version" {
  secret      = google_secret_manager_secret.linkedin_client_secret.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "DATABASE_URL"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url_initial_version" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "placeholder-db-url"
}

resource "google_secret_manager_secret" "zyte_api_key" {
  secret_id = "ZYTE_API_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "zyte_api_key_initial_version" {
  secret      = google_secret_manager_secret.zyte_api_key.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "openrouter_model_primary" {
  secret_id = "OPENROUTER_MODEL_PRIMARY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_model_primary_initial_version" {
  secret      = google_secret_manager_secret.openrouter_model_primary.id
  secret_data = "google/gemini-2.5-flash"
}

resource "google_secret_manager_secret" "openrouter_models_fallback" {
  secret_id = "OPENROUTER_MODELS_FALLBACK"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_models_fallback_initial_version" {
  secret      = google_secret_manager_secret.openrouter_models_fallback.id
  secret_data = "deepseek/deepseek-chat-v3-0324"
}

resource "google_secret_manager_secret" "openrouter_model_temperature" {
  secret_id = "OPENROUTER_MODEL_TEMPERATURE"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_model_temperature_initial_version" {
  secret      = google_secret_manager_secret.openrouter_model_temperature.id
  secret_data = "0.0"
}

resource "google_secret_manager_secret" "openrouter_large_model_primary" {
  secret_id = "OPENROUTER_LARGE_MODEL_PRIMARY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_large_model_primary_initial_version" {
  secret      = google_secret_manager_secret.openrouter_large_model_primary.id
  secret_data = "google/gemini-2.5-pro"
}

resource "google_secret_manager_secret" "openrouter_large_models_fallback" {
  secret_id = "OPENROUTER_LARGE_MODELS_FALLBACK"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_large_models_fallback_initial_version" {
  secret      = google_secret_manager_secret.openrouter_large_models_fallback.id
  secret_data = "anthropic/claude-sonnet-4"
}

resource "google_secret_manager_secret" "openrouter_large_model_temperature" {
  secret_id = "OPENROUTER_LARGE_MODEL_TEMPERATURE"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openrouter_large_model_temperature_initial_version" {
  secret      = google_secret_manager_secret.openrouter_large_model_temperature.id
  secret_data = "0.0"
}

resource "google_secret_manager_secret" "apify_api_key" {
  secret_id = "APIFY_API_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "apify_api_key_initial_version" {
  secret      = google_secret_manager_secret.apify_api_key.id
  secret_data = "placeholder"
}

resource "google_secret_manager_secret" "post_media_bucket_name" {
  secret_id = "POST_MEDIA_BUCKET_NAME"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "post_media_bucket_name_initial_version" {
  secret      = google_secret_manager_secret.post_media_bucket_name.id
  secret_data = google_storage_bucket.post_media_bucket.name
  depends_on = [
    google_storage_bucket.post_media_bucket
  ]
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
    gcp_generate_suggestions_function_url = google_secret_manager_secret.gcp_generate_suggestions_function_url
    openrouter_api_key    = google_secret_manager_secret.openrouter_api_key
    linkedin_client_id    = google_secret_manager_secret.linkedin_client_id
    linkedin_client_secret = google_secret_manager_secret.linkedin_client_secret
    database_url          = google_secret_manager_secret.database_url
    zyte_api_key          = google_secret_manager_secret.zyte_api_key
    apify_api_key         = google_secret_manager_secret.apify_api_key
    post_media_bucket_name = google_secret_manager_secret.post_media_bucket_name
  }

  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.app_sa.email}"
}

module "cloud_run_service" {
  count  = var.manage_cloud_run_service ? 1 : 0
  source = "../modules/cloud-run-service"

  project_id                 = var.project_id
  region                     = var.region
  app_name                   = var.app_name
  environment                = var.environment
  cloud_run_min_instances    = var.cloud_run_min_instances
  cloud_run_max_instances    = var.cloud_run_max_instances
  cloud_run_cpu              = var.cloud_run_cpu
  cloud_run_memory           = var.cloud_run_memory
  service_account_email      = data.google_service_account.app_sa.email
  docker_registry_location   = var.docker_registry_location
  backend_repo_repository_id = google_artifact_registry_repository.backend_repo.repository_id
  cors_origins               = local.cors_origins
  frontend_url               = local.frontend_url
  backend_url                = local.backend_url
  gcp_project_id             = var.project_id
  gcp_location               = var.region
  jwt_secret_name            = google_secret_manager_secret.jwt_secret.secret_id
  supabase_url_name          = google_secret_manager_secret.supabase_url.secret_id
  supabase_key_name          = google_secret_manager_secret.supabase_key.secret_id
  supabase_service_key_name  = google_secret_manager_secret.supabase_service_key.secret_id
  google_client_id_name      = google_secret_manager_secret.google_client_id.secret_id
  google_client_secret_name  = google_secret_manager_secret.google_client_secret.secret_id
  gcp_analysis_function_url_name = google_secret_manager_secret.gcp_analysis_function_url.secret_id
  gcp_analysis_function_url_version = google_secret_manager_secret_version.gcp_analysis_function_url_initial_version.version
  openrouter_api_key_name    = google_secret_manager_secret.openrouter_api_key.secret_id
  linkedin_client_id_name    = google_secret_manager_secret.linkedin_client_id.secret_id
  linkedin_client_secret_name = google_secret_manager_secret.linkedin_client_secret.secret_id
  database_url_name          = google_secret_manager_secret.database_url.secret_id
  post_media_bucket_name_name = google_secret_manager_secret.post_media_bucket_name.secret_id
  openrouter_model_primary_name = google_secret_manager_secret.openrouter_model_primary.secret_id
  openrouter_models_fallback_name = google_secret_manager_secret.openrouter_models_fallback.secret_id
  openrouter_model_temperature_name = google_secret_manager_secret.openrouter_model_temperature.secret_id
  openrouter_large_model_primary_name = google_secret_manager_secret.openrouter_large_model_primary.secret_id
  openrouter_large_models_fallback_name = google_secret_manager_secret.openrouter_large_models_fallback.secret_id
  openrouter_large_model_temperature_name = google_secret_manager_secret.openrouter_large_model_temperature.secret_id
  allow_unauthenticated_invocations = false
}

# --- Frontend Infrastructure (GCS Bucket + CDN for Static Site) ---

locals {
  is_production   = var.environment == "production"
  frontend_domain = var.frontend_domain_name
  backend_domain  = "api.${var.frontend_domain_name}"
  frontend_url    = "https://${var.frontend_domain_name}"
  backend_url     = "https://api.${var.frontend_domain_name}"
  
  # Default CORS origins if none provided
  cors_origins = concat(
    ["https://${var.frontend_domain_name}"],
    var.environment == "staging" ? [
      # Include additional domains for staging
      "https://staging.${var.frontend_domain_name}",
    ] : []
  )
}

# 1. Cloud Storage bucket to host static files
resource "google_storage_bucket" "frontend_bucket" {
  count = var.manage_frontend_infra ? 1 : 0

  name          = "${local.frontend_domain}" # Bucket names must be globally unique
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

  depends_on = [google_project_service.application_apis]
}

# 2. Grant public read access to the bucket objects for the CDN
data "google_iam_policy" "public_bucket_policy" {
  binding {
    role    = "roles/storage.objectViewer"
    members = ["allUsers"]
  }
}

resource "google_storage_bucket_iam_policy" "public_access" {
  count = var.manage_frontend_infra ? 1 : 0

  bucket      = google_storage_bucket.frontend_bucket[0].name
  policy_data = data.google_iam_policy.public_bucket_policy.policy_data

  depends_on = [google_storage_bucket.frontend_bucket]
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
    negative_caching     = false
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
  count       = var.manage_dns_zone ? 1 : 0
  name        = "promptly-social-zone"
  dns_name    = "promptly.social."
  description = "DNS zone for promptly.social"
  project     = var.project_id

  cloud_logging_config {
    enable_logging = false
  }
}

# DNS IAM permissions are managed by bootstrap module

resource "google_dns_record_set" "frontend_a_record" {
  count = var.manage_frontend_infra ? 1 : 0

  managed_zone = local.is_production ? google_dns_managed_zone.frontend_zone[0].name : data.google_dns_managed_zone.production_zone[0].name
  name         = "${local.frontend_domain}."
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.frontend_ip[0].address]
  project      = local.is_production ? var.project_id : var.production_project_id
}

# --- MX Records for Email ---

# NOTE: The following records are for Google Workspace.
# If you use a different email provider, you MUST update these records
# with the values provided by your provider.
resource "google_dns_record_set" "mx_records" {
  count = var.manage_frontend_infra ? 1 : 0

  managed_zone = local.is_production ? google_dns_managed_zone.frontend_zone[0].name : data.google_dns_managed_zone.production_zone[0].name
  name         = "${local.frontend_domain}."
  type         = "MX"
  ttl          = 3600
  rrdatas = [
    "1 ASPMX.L.GOOGLE.COM.",
    "5 ALT1.ASPMX.L.GOOGLE.COM.",
    "5 ALT2.ASPMX.L.GOOGLE.COM.",
    "10 ASPMX2.GOOGLEMAIL.COM.",
    "10 ASPMX3.GOOGLEMAIL.COM.",
  ]
  project = local.is_production ? var.project_id : var.production_project_id
}

# --- Backend API Infrastructure (Load Balancer for Cloud Run) ---

# 1. Serverless NEG for the Cloud Run service
resource "google_compute_region_network_endpoint_group" "backend_neg" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0

  name                  = "${var.app_name}-backend-neg-${var.environment}"
  network_endpoint_type = "SERVERLESS"
  region                = module.cloud_run_service[0].service_location
  cloud_run {
    service = module.cloud_run_service[0].service_name
  }
}

# 2. Backend Service
resource "google_compute_backend_service" "api_backend" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0

  name                  = "${var.app_name}-api-backend-service-${var.environment}"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  timeout_sec           = 30
  enable_cdn            = false

  backend {
    group = google_compute_region_network_endpoint_group.backend_neg[0].id
  }
}

# 3. Reserve a static IP for the API load balancer
resource "google_compute_global_address" "api_ip" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0
  name  = "${var.app_name}-api-ip-${var.environment}"
}

# 4. Managed SSL Certificate for the API domain
resource "google_compute_managed_ssl_certificate" "api_ssl" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0
  name  = "${var.app_name}-api-ssl-${var.environment}"
  managed {
    domains = [local.backend_domain]
  }
}

# 5. URL Map to route all requests to the API backend service
resource "google_compute_url_map" "api_url_map" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0

  name            = "${var.app_name}-api-url-map-${var.environment}"
  default_service = google_compute_backend_service.api_backend[0].id
}

# 6. HTTPS Target Proxy
resource "google_compute_target_https_proxy" "api_https_proxy" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0

  name             = "${var.app_name}-api-https-proxy-${var.environment}"
  url_map          = google_compute_url_map.api_url_map[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.api_ssl[0].id]
}

# 7. Global Forwarding Rule (Load Balancer Frontend for API)
resource "google_compute_global_forwarding_rule" "api_forwarding_rule" {
  count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0

  name                  = "${var.app_name}-api-forwarding-rule-${var.environment}"
  target                = google_compute_target_https_proxy.api_https_proxy[0].id
  ip_address            = google_compute_global_address.api_ip[0].address
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

  # 8. DNS A record for the API (points to Load Balancer IP)
  resource "google_dns_record_set" "api_a_record" {
    count = var.manage_cloud_run_service && var.manage_backend_load_balancer ? 1 : 0

    managed_zone = local.is_production ? google_dns_managed_zone.frontend_zone[0].name : data.google_dns_managed_zone.production_zone[0].name
    name         = "${local.backend_domain}."
    type         = "A"
    ttl          = 300
    rrdatas      = [google_compute_global_address.api_ip[0].address]
    project      = local.is_production ? var.project_id : var.production_project_id
  }

# Grant Cloud Scheduler SA permission to invoke Cloud Run backend
resource "google_cloud_run_service_iam_member" "scheduler_invoker" {
  count    = var.manage_cloud_run_service ? 1 : 0

  project  = var.project_id
  location = module.cloud_run_service[0].service_location
  service  = module.cloud_run_service[0].service_name

  role   = "roles/run.invoker"
  member = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"

  depends_on = [module.cloud_run_service]
}

# Allow Cloud Scheduler SA to impersonate the App service account for OIDC token generation
resource "google_service_account_iam_member" "scheduler_impersonates_app_sa" {
  count = var.manage_cloud_run_service ? 1 : 0

  service_account_id = data.google_service_account.app_sa.name
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
  role               = "roles/iam.serviceAccountTokenCreator"
}

# Allow App service account to actAs itself (needed when it creates Scheduler jobs with oidc_token)
resource "google_service_account_iam_member" "app_sa_self_actas" {
  service_account_id = data.google_service_account.app_sa.name
  member             = "serviceAccount:${data.google_service_account.app_sa.email}"
  role               = "roles/iam.serviceAccountUser"
}

resource "google_project_iam_member" "scheduler_logging_writer" {
  project = var.project_id
  role = "roles/logging.logWriter"
  member = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}