# Production Environment Outputs

# Infrastructure module outputs
output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = module.infrastructure.cloud_run_service_url
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = module.infrastructure.cloud_run_service_name
}

output "frontend_bucket_name" {
  description = "Name of the frontend storage bucket"
  value       = module.infrastructure.frontend_bucket_name
}

output "frontend_bucket_url" {
  description = "URL of the frontend storage bucket"
  value       = module.infrastructure.frontend_bucket_url
}

output "cdn_url" {
  description = "URL of the CDN"
  value       = module.infrastructure.cdn_url
}

output "api_load_balancer_ip" {
  description = "IP address of the API load balancer"
  value       = module.infrastructure.api_load_balancer_ip
}

output "dns_zone_nameservers" {
  description = "Name servers for the DNS zone"
  value       = module.infrastructure.dns_zone_nameservers
}

output "artifact_registry_repository_url" {
  description = "URL of the Artifact Registry repository"
  value       = module.infrastructure.artifact_registry_repository_url
}
