output "dns_zone_nameservers" {
  description = "The list of nameservers for the managed zone."
  value       = var.create_zone ? google_dns_managed_zone.frontend_zone[0].name_servers : null
}

output "dns_zone_name" {
  description = "The name of the managed zone."
  value       = var.create_zone ? google_dns_managed_zone.frontend_zone[0].name : var.managed_zone_name
}
