variable "project_id" {
  description = "The ID of your Google Cloud project."
  type        = string
}

variable "staging_project_id" {
  description = "The ID of the staging Google Cloud project. Required for production to grant cross-project DNS access."
  type        = string
  default     = null
}

variable "github_repo" {
  description = "Your GitHub repository in owner/repo format (e.g., 'my-org/my-repo')."
  type        = string
}

variable "app_name" {
  description = "A short name for your application, used for naming resources."
  type        = string
  default     = "promptly"
}

variable "dns_reader_sds" {
  description = "List of service accounts to grant dns.reader role to"
  type        = list(string)
  default     = []
}

variable "terraform_state_bucket_name" {
  description = "The name for the GCS bucket that will store Terraform state."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., staging, production)."
  type        = string
} 