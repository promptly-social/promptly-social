# Backend configuration for staging monitoring
terraform {
  backend "gcs" {
    bucket = "promptly-terraform-states"
    prefix = "terraform/state/gcp-functions/unified-post-scheduler/staging"
  }
}
