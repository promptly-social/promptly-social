# terraform/modules/bootstrap/main.tf

# 1. Enable required APIs for this setup.
resource "google_project_service" "iam_api" {
  project                    = var.project_id
  service                    = "iam.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "storage_api" {
  project                    = var.project_id
  service                    = "storage.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "iam_credentials_api" {
  project                    = var.project_id
  service                    = "iamcredentials.googleapis.com"
  disable_dependent_services = true
}

# 2. Create the Workload Identity Pool. This is the trust boundary.
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.project_id
  workload_identity_pool_id = "${var.app_name}-github-pool-${var.environment}"
  display_name              = "${var.app_name} WIF Pool (${var.environment})"
  description               = "Allows GitHub Actions to securely authenticate with GCP for ${var.environment}"
  depends_on                = [google_project_service.iam_api]
}

# 3. Create the OIDC Provider for the pool, specifying GitHub as the trusted issuer.
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
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

# Create GCS bucket to store Terraform state
resource "google_storage_bucket" "terraform_state" {
  project       = var.project_id
  name          = var.terraform_state_bucket_name
  location      = "US" # Or another location of your choice
  storage_class = "STANDARD"

  # It's best practice to enable versioning on state buckets
  versioning {
    enabled = true
  }

  # Prevent accidental deletion of the state bucket
  force_destroy = false

  # Use uniform bucket-level access for simpler and more secure IAM
  uniform_bucket_level_access = true

  # Ensure the bucket is created after the necessary API is enabled
  depends_on = [google_project_service.storage_api]
}

# 4. Create a dedicated Service Account for Terraform to use in CI/CD.
resource "google_service_account" "terraform_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-tf-sa-${var.environment}"
  display_name = "Terraform CI/CD SA (${var.environment})"
  depends_on   = [google_project_service.iam_api]
}

# Grant the Terraform SA permissions to manage the state bucket
resource "google_storage_bucket_iam_member" "terraform_sa_state_bucket_admin" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# 5. Grant the Terraform SA the necessary permissions to manage your project's resources.
# Using granular roles instead of the overly broad 'roles/owner' for better security.
resource "google_project_iam_member" "terraform_sa_roles" {
  for_each = toset([
    # Core project management
    "roles/serviceusage.serviceUsageAdmin",     # Manage API services

    # Service Account management
    "roles/iam.serviceAccountAdmin",            # Create/manage service accounts
    "roles/iam.serviceAccountKeyAdmin",         # Manage service account keys
    "roles/iam.securityAdmin",                  # Manage IAM policies and bindings
    "roles/iam.workloadIdentityPoolAdmin",      # Manage Workload Identity pools

    # Artifact Registry
    "roles/artifactregistry.admin",             # Manage Artifact Registry repositories
    "roles/artifactregistry.writer",            # Write Artifact Registry repositories

    # Secret Manager
    "roles/secretmanager.admin",                # Create and manage secrets

    # Cloud Run
    "roles/run.admin",                          # Manage Cloud Run services

    # Cloud Functions (for the separate GCP function)
    "roles/cloudfunctions.admin",               # Manage Cloud Functions
    "roles/cloudbuild.builds.editor",           # Build functions

    # Storage (for function source code)
    "roles/storage.admin",                      # Manage Cloud Storage buckets

    # Compute (for domain mappings and networking)
    "roles/compute.networkAdmin",               # Manage networking resources

    # DNS (for managing domain records)
    "roles/dns.admin",                          # Manage Cloud DNS zones and records

    # Monitoring and Logging (for observability resources)
    "roles/logging.admin",                      # Manage logging resources
    "roles/monitoring.admin"                    # Manage monitoring resources
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# 6. Allow GitHub Actions from your repository to impersonate the Terraform Service Account.
resource "google_service_account_iam_binding" "terraform_sa_wif_binding" {
  service_account_id = google_service_account.terraform_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}",
  ]
  depends_on = [
    google_project_service.iam_credentials_api,
    google_iam_workload_identity_pool_provider.github_provider,
  ]
}

resource "google_project_iam_member" "dns_readers" {
  count    = var.environment == "production" ? length(var.dns_reader_sds) : 0
  project  = var.project_id
  role     = "roles/dns.reader"
  member   = "serviceAccount:${var.dns_reader_sds[count.index]}"
}