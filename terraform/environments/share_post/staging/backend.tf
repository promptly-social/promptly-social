terraform {
  backend "gcs" {
    bucket = "promptly-social-tf-state-staging"
    prefix = "share-post"
  }
}