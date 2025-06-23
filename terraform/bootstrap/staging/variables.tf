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

variable "bootstrap_admins" {
  type        = list(string)
  description = "Users allowed to impersonate the Terraform SA locally"
}
