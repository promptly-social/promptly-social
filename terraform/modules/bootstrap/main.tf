# terraform/modules/bootstrap/main.tf
# This module handles foundational setup: service accounts, WIF, state bucket, and basic IAM

# 1. Enable required APIs for bootstrap setup
resource "google_project_service" "required_apis" {
  for_each = toset([
    "iam.googleapis.com",
    "storage.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ])

  project                    = var.project_id
  service                    = each.value
  disable_dependent_services = false
}

# 2. Create the Workload Identity Pool for GitHub Actions authentication
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool-${var.environment}"
  display_name              = "GitHub WIF Pool (${var.environment})"
  description               = "Workload Identity Federation pool for GitHub Actions in ${var.environment}"
  
  depends_on = [google_project_service.required_apis]
}

# 3. Create the OIDC Provider for GitHub Actions
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "gh-provider"
  display_name                       = "GitHub Actions OIDC Provider"
  description                        = "OIDC provider for GitHub Actions authentication"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.actor"      = "assertion.actor"
    "attribute.ref"        = "assertion.ref"
  }
  
  attribute_condition = "assertion.repository_owner == 'promptly-social'"
  
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  
  depends_on = [google_iam_workload_identity_pool.github_pool]
}

# 4. Create GCS bucket for Terraform state storage
resource "google_storage_bucket" "terraform_state" {
  project       = var.project_id
  name          = var.terraform_state_bucket_name
  location      = var.state_bucket_location
  storage_class = "STANDARD"

  # Enable versioning for state file history
  versioning {
    enabled = true
  }

  # Prevent accidental deletion
  force_destroy = false

  # Use uniform bucket-level access for better security
  uniform_bucket_level_access = true

  # Enable object lifecycle management
  lifecycle_rule {
    condition {
      age = 30
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis]
}

# 5. Create dedicated service accounts
# Terraform Service Account for CI/CD operations
resource "google_service_account" "terraform_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-tf-sa-${var.environment}"
  display_name = "Terraform CI/CD Service Account (${var.environment})"
  description  = "Service account used by Terraform for infrastructure management in ${var.environment}"
  
  depends_on = [google_project_service.required_apis]
}

# Application Service Account for runtime operations
resource "google_service_account" "app_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-app-sa-${var.environment}"
  display_name = "Application Service Account (${var.environment})"
  description  = "Service account used by the application runtime in ${var.environment}"
  
  depends_on = [google_project_service.required_apis]
}

# 6. Grant Terraform SA access to state bucket
resource "google_storage_bucket_iam_member" "terraform_sa_state_bucket_admin" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# 7. Allow Terraform SA to impersonate Application SA
# This enables Terraform to deploy resources that run as the App SA
resource "google_service_account_iam_member" "terraform_sa_impersonates_app_sa" {
  service_account_id = google_service_account.app_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# Allow Terraform SA to create access tokens for App SA
resource "google_project_iam_member" "terraform_sa_roles" {
  for_each = toset([
    # Core project and API management
    "roles/serviceusage.serviceUsageAdmin",     # Enable/disable APIs
    "roles/resourcemanager.projectIamAdmin",    # Manage project IAM
    
    # Service Account management
    "roles/iam.serviceAccountAdmin",            # Create/manage service accounts
    "roles/iam.serviceAccountUser",             # Impersonate service accounts
    "roles/iam.serviceAccountTokenCreator",     # Create access tokens
    "roles/iam.workloadIdentityUser",           # Use Workload Identity
    
    # Application infrastructure
    "roles/run.admin",                          # Cloud Run services
    "roles/secretmanager.admin",                # Secret Manager
    "roles/artifactregistry.admin",             # Artifact Registry
    "roles/cloudbuild.builds.editor",           # Cloud Build
    "roles/storage.admin",                      # Cloud Storage
    "roles/cloudfunctions.admin",              # Cloud Functions admin (read/manage functions)
    
    # Networking and DNS
    "roles/compute.networkAdmin",               # Networking resources
    "roles/compute.loadBalancerAdmin",          # Load balancers
    "roles/dns.admin",                          # DNS management
    
    # Monitoring and operations
    "roles/logging.admin",                      # Cloud Logging
    "roles/monitoring.admin",                   # Cloud Monitoring
    "roles/cloudscheduler.admin"                # Cloud Scheduler

    
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# 9. Configure Workload Identity Federation for GitHub Actions
# Allow GitHub Actions to impersonate Terraform SA
resource "google_service_account_iam_binding" "terraform_sa_wif_binding" {
  service_account_id = google_service_account.terraform_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}",
  ]
  
  depends_on = [
    google_iam_workload_identity_pool_provider.github_provider,
  ]
}

# Allow GitHub Actions to generate access tokens for Terraform SA
resource "google_service_account_iam_binding" "terraform_sa_token_creator" {
  service_account_id = google_service_account.terraform_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}",
  ]
  
  depends_on = [
    google_service_account_iam_binding.terraform_sa_wif_binding,
  ]
}

# 10. Cross-project DNS access (production only)
resource "google_project_iam_member" "dns_readers" {
  count   = var.environment == "production" ? length(var.dns_reader_service_accounts) : 0
  project = var.project_id
  role    = "roles/dns.reader"
  member  = "serviceAccount:${var.dns_reader_service_accounts[count.index]}"
}

# 11. Allow bootstrap admins to impersonate Terraform SA locally
resource "google_service_account_iam_member" "tf_sa_admin_user" {
  for_each           = toset(var.bootstrap_admins)
  service_account_id = google_service_account.terraform_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${each.value}"
}

resource "google_service_account_iam_member" "tf_sa_admin_token_creator" {
  for_each           = toset(var.bootstrap_admins)
  service_account_id = google_service_account.terraform_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "user:${each.value}"
}

# 12. Allow Terraform SA to impersonate Compute Engine default SA
# Required for Cloud Build and other services that use the default compute SA
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_service_account_iam_member" "terraform_sa_impersonate_compute_sa" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.terraform_sa.email}"
}