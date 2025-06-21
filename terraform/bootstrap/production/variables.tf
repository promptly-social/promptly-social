variable "project_id" {
  description = "The ID of your Google Cloud project."
  type        = string
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

variable "staging_project_id" {
  description = "The ID of the staging Google Cloud project. Required for production to grant cross-project DNS access."
  type        = string
  default     = "promptly-social-staging"
}