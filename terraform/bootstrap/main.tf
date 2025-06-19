# terraform/bootstrap/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # This configuration is meant for a one-time, local execution.
  # The backend is intentionally local.
  backend "local" {}
}

provider "google" {
  project = var.project_id
}

variable "project_id" {
  description = "The ID of your Google Cloud project."
  type        = string
}

variable "github_repo" {
  description = "Your GitHub repository in owner/repo format (e.g., 'my-org/my-repo')."
  type        = string
}

variable "app_name" {
  description = "A short name for your application, used for naming resources."
  type        = string
  default     = "promptly"
}

# 1. Enable required APIs for this setup.
resource "google_project_service" "iam_api" {
  project                    = var.project_id
  service                    = "iam.googleapis.com"
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
  workload_identity_pool_id = "${var.app_name}-github-pool"
  display_name              = "WIF Pool for ${var.app_name}"
  description               = "Allows GitHub Actions to securely authenticate with GCP"
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
  attribute_condition = "attribute.repository == '${var.github_repo}'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 4. Create a dedicated Service Account for Terraform to use in CI/CD.
resource "google_service_account" "terraform_sa" {
  project      = var.project_id
  account_id   = "${var.app_name}-terraform-sa"
  display_name = "Terraform CI/CD Service Account"
  depends_on   = [google_project_service.iam_api]
}

# 5. Grant the Terraform SA the necessary permissions to manage your project's resources.
# For simplicity, we use 'roles/owner'. In a high-security environment, you should
# grant a granular set of roles (e.g., roles/run.admin, roles/storage.admin, etc.).
resource "google_project_iam_member" "terraform_sa_roles" {
  project = var.project_id
  role    = "roles/owner"
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

# --- Outputs ---
# These values will be used to configure GitHub secrets for your CI/CD pipelines.

output "gcp_project_id" {
  description = "The GCP Project ID."
  value       = var.project_id
}

output "workload_identity_provider" {
  description = "The full ID of the Workload Identity Provider for GitHub Actions."
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "terraform_service_account_email" {
  description = "The email of the service account created for Terraform CI/CD."
  value       = google_service_account.terraform_sa.email
} 