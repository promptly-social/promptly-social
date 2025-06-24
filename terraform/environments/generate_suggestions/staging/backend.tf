terraform {
  backend "gcs" {
    bucket = "promptly-terraform-states"
    prefix = "terraform/state/gcp-functions/generate-suggestions/staging"
  }
} 