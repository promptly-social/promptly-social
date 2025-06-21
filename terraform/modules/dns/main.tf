# This creates a managed zone for 'promptly.social'.
# NOTE: After running this, you must update the nameservers at your
# domain registrar to the ones provided in the `dns_zone_nameservers` output.
resource "google_dns_managed_zone" "frontend_zone" {
  name        = var.dns_zone_name
  dns_name    = var.dns_domain_name
  project     = var.project_id
  description = "DNS zone for ${var.dns_domain_name}"
}

resource "google_project_iam_member" "dns_editors" {
  for_each = toset(var.dns_editor_service_accounts)
  project  = var.project_id
  role     = "roles/dns.admin"
  member   = "serviceAccount:${each.key}"
}

resource "google_dns_record_set" "frontend_a_record" {
  managed_zone = google_dns_managed_zone.frontend_zone.name
  name         = "${var.frontend_domain_name}."
  type         = "A"
  ttl          = 300
  rrdatas      = [var.frontend_ip_address]
  project      = var.project_id
}

resource "google_dns_record_set" "api_a_record" {
  managed_zone = google_dns_managed_zone.frontend_zone.name
  name         = "${var.backend_domain_name}."
  type         = "A"
  ttl          = 300
  rrdatas      = [var.api_ip_address]
  project      = var.project_id
}
