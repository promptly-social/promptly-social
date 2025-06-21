variable "project_id" {
  description = "The ID of the project in which to manage DNS resources."
  type        = string
}

variable "dns_zone_name" {
  description = "A name for the managed zone in GCP."
  type        = string
  default     = "promptly-social-zone"
}

variable "dns_domain_name" {
  description = "The actual domain name for the DNS zone."
  type        = string
  default     = "promptly.social."
}

variable "dns_editor_service_accounts" {
  description = "A list of service accounts to grant DNS admin role."
  type        = list(string)
  default     = []
}

variable "frontend_domain_name" {
  description = "The domain name for the frontend."
  type        = string
}

variable "frontend_ip_address" {
  description = "The external IP address for the frontend."
  type        = string
}

variable "backend_domain_name" {
  description = "The domain name for the backend API."
  type        = string
}

variable "api_ip_address" {
  description = "The external IP address for the backend API."
  type        = string
}
