# Backend configuration for production monitoring
terraform {
  backend "gcs" {
    bucket = "promptly-social-terraform-state"
    prefix = "monitoring"
  }
}
