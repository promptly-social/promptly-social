terraform {
  backend "gcs" {
    bucket = "promptly-social-tf-state-production"
    prefix = "share-post"
  }
}