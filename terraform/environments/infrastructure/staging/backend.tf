terraform {
  backend "gcs" {
    bucket = "promptly-terraform-states"
    prefix = "terraform/state/staging"
  }
} 