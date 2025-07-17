terraform {
  backend "gcs" {
    bucket = "promptly-terraform-state"
    prefix = "terraform/state/gcp-functions/share-post/production"
  }
}