# This creates a managed zone for 'promptly.social', but only if var.create_zone is true.
resource "google_dns_managed_zone" "frontend_zone" {
  count = var.create_zone ? 1 : 0

  name        = var.dns_zone_name
  dns_name    = var.dns_domain_name
  description = "DNS zone for ${var.dns_domain_name}"
}

# Creates a DNS A record for the frontend if an IP address is provided.
resource "google_dns_record_set" "frontend_a_record" {
  count = var.frontend_ip_address != "" ? 1 : 0

  managed_zone = var.managed_zone_name
  name         = "${var.frontend_domain_name}."
  type         = "A"
  ttl          = 300
  rrdatas      = [var.frontend_ip_address]
}

# Creates a DNS A record for the backend API if an IP address is provided.
resource "google_dns_record_set" "api_cname_record" {
  count = var.api_ip_address != "" ? 1 : 0

  managed_zone = var.managed_zone_name
  name         = "${var.backend_domain_name}."
  type         = "CNAME"
  ttl          = 300
  rrdatas      = ["ghs.googlehosted.com."]
}
