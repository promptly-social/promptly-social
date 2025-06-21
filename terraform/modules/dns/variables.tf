variable "create_zone" {
  description = "Whether to create the DNS managed zone."
  type        = bool
  default     = false
}

variable "managed_zone_name" {
  description = "The name of the managed zone to add records to."
  type        = string
}

variable "dns_zone_name" {
  description = "A name for the managed zone in GCP (used for creation)."
  type        = string
  default     = "promptly-social-zone"
}

variable "dns_domain_name" {
  description = "The actual domain name for the DNS zone (used for creation)."
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
  description = "The external IP address for the frontend. If empty, no record is created."
  type        = string
  default     = ""
}

variable "backend_domain_name" {
  description = "The domain name for the backend API."
  type        = string
}

variable "api_ip_address" {
  description = "The external IP address for the backend API. If empty, no record is created."
  type        = string
  default     = ""
}
