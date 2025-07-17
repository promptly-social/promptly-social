terraform {
  backend "gcs" {
    bucket = "promptly-terraform-state"
    prefix = "terraform/state/gcp-functions/unified-post-scheduler/production"
  }
}