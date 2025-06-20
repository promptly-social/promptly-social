# --- DNS for Backend API ---
# Create DNS records for the Cloud Run custom domain.
# We create separate resources for each record type to avoid issues with
# for_each on computed values from the Cloud Run module output.

locals {
  # This local block is now scoped to the DNS configuration
  _api_dns_records_list = var.manage_cloud_run_service && length(google_cloud_run_domain_mapping.api_domain_mapping) > 0 ? google_cloud_run_domain_mapping.api_domain_mapping[0].status[0].resource_records : []

  _a_rrdatas     = [for r in local._api_dns_records_list : r.rrdata if r.type == "A"]
  _aaaa_rrdatas  = [for r in local._api_dns_records_list : r.rrdata if r.type == "AAAA"]
  _cname_rrdatas = [for r in local._api_dns_records_list : r.rrdata if r.type == "CNAME"]
  _cname_name    = try([for r in local._api_dns_records_list : r.name if r.type == "CNAME"][0], null)
}


resource "google_dns_record_set" "api_a_records" {
  count = length(local._a_rrdatas) > 0 ? 1 : 0

  managed_zone = google_dns_managed_zone.frontend_zone[0].name
  name         = "${local.api_domain}."
  type         = "A"
  ttl          = 300
  rrdatas      = local._a_rrdatas
  project      = var.project_id
}

resource "google_dns_record_set" "api_aaaa_records" {
  count = length(local._aaaa_rrdatas) > 0 ? 1 : 0

  managed_zone = google_dns_managed_zone.frontend_zone[0].name
  name         = "${local.api_domain}."
  type         = "AAAA"
  ttl          = 300
  rrdatas      = local._aaaa_rrdatas
  project      = var.project_id
}

resource "google_dns_record_set" "api_cname_records" {
  count = local._cname_name != null && length(local._cname_rrdatas) > 0 ? 1 : 0

  managed_zone = google_dns_managed_zone.frontend_zone[0].name
  name         = "${local._cname_name}."
  type         = "CNAME"
  ttl          = 300
  rrdatas      = local._cname_rrdatas
  project      = var.project_id
} 