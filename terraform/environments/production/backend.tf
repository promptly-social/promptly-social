terraform {
  backend "gcs" {
    bucket = ""  # Will be set via -backend-config or environment variables
    prefix = "terraform/state/production"
  }
} 