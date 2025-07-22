# Backend configuration for staging monitoring
terraform {
  backend "gcs" {
    bucket = "promptly-social-staging-terraform-state"
    prefix = "monitoring"
  }
}
