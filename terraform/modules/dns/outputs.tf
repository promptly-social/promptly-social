output "dns_zone_nameservers" {
  description = "The list of nameservers for the managed zone."
  value       = google_dns_managed_zone.frontend_zone.name_servers
}

output "dns_zone_name" {
  description = "The name of the managed zone."
  value       = google_dns_managed_zone.frontend_zone.name
}
