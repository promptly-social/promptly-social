variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy the function to."
  type        = string
  default     = "us-central1"
} 