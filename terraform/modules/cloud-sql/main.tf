# Cloud SQL PostgreSQL Instance Module
# This module creates a secure Cloud SQL PostgreSQL instance with proper networking and security configurations

# Random password generation for database users
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.app_name}-${var.environment}-db"
  database_version = var.database_version
  region          = var.region
  project         = var.project_id

  deletion_protection = var.deletion_protection

  settings {
    tier                        = var.tier
    disk_size                  = var.disk_size
    disk_type                  = var.disk_type
    disk_autoresize           = var.disk_autoresize
    disk_autoresize_limit     = var.disk_autoresize_limit
    availability_type         = var.availability_type
    
    backup_configuration {
      enabled                        = var.backup_enabled
      start_time                    = var.backup_start_time
      point_in_time_recovery_enabled = var.point_in_time_recovery
      backup_retention_settings {
        retained_backups = var.backup_retention_count
        retention_unit   = "COUNT"
      }
      transaction_log_retention_days = var.transaction_log_retention_days
    }

    maintenance_window {
      day          = var.maintenance_window_day
      hour         = var.maintenance_window_hour
      update_track = var.maintenance_window_update_track
    }

    ip_configuration {
      ipv4_enabled                                  = var.private_network == null ? true : var.ipv4_enabled
      private_network                              = var.private_network
      enable_private_path_for_google_cloud_services = var.private_network != null ? var.enable_private_path : false
      ssl_mode                                     = var.require_ssl ? "ENCRYPTED_ONLY" : "ALLOW_UNENCRYPTED_AND_ENCRYPTED"

      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    database_flags {
      name  = "log_temp_files"
      value = "0"
    }

    insights_config {
      query_insights_enabled  = var.query_insights_enabled
      record_application_tags = var.record_application_tags
      record_client_address   = var.record_client_address
    }
  }

  depends_on = [
    google_project_service.sqladmin
  ]
}

# Enable Cloud SQL Admin API
resource "google_project_service" "sqladmin" {
  project = var.project_id
  service = "sqladmin.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

# Main application database
resource "google_sql_database" "main_database" {
  name     = "${var.app_name}_${var.environment}"
  instance = google_sql_database_instance.main.name
  project  = var.project_id

  depends_on = [google_sql_database_instance.main]
}

# Database user for application
resource "google_sql_user" "app_user" {
  name     = "${var.app_name}_app_user"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
  project  = var.project_id

  depends_on = [google_sql_database_instance.main]
}


# Database connection URL secret
resource "google_secret_manager_secret" "db_url" {
  secret_id = "DATABASE_URL"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_url" {
  secret = google_secret_manager_secret.db_url.id
  secret_data = "postgresql://${google_sql_user.app_user.name}:${random_password.db_password.result}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.main_database.name}?sslmode=require"

  depends_on = [
    google_sql_database_instance.main,
    google_sql_database.main_database,
    google_sql_user.app_user
  ]
}

# Database username secret
resource "google_secret_manager_secret" "db_username" {
  secret_id = "CLOUD_SQL_USER"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_username" {
  secret = google_secret_manager_secret.db_username.id
  secret_data = google_sql_user.app_user.name

  depends_on = [google_sql_user.app_user]
}

# Database password secret
resource "google_secret_manager_secret" "db_password" {
  secret_id = "CLOUD_SQL_PASSWORD"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result

  depends_on = [random_password.db_password]
}

resource "google_secret_manager_secret" "db_instance_connection_name" {
  secret_id = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_instance_connection_name" {
  secret = google_secret_manager_secret.db_instance_connection_name.id
  secret_data = google_sql_database_instance.main.connection_name

  depends_on = [google_sql_database_instance.main]
}

resource "google_secret_manager_secret" "db_name" {
  secret_id = "CLOUD_SQL_DATABASE_NAME"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "db_name" {
  secret = google_secret_manager_secret.db_name.id
  secret_data = google_sql_database_instance.main.connection_name

  depends_on = [google_sql_database_instance.main]
}


# Enable Secret Manager API
resource "google_project_service" "secretmanager" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_dependent_services = false
  disable_on_destroy        = false
}

# IAM bindings for Terraform SA (Cloud SQL Admin permissions)
resource "google_project_iam_member" "terraform_sa_cloudsql_admin" {
  project = var.project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${var.terraform_sa_email}"
}

resource "google_project_iam_member" "terraform_sa_secretmanager_admin" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${var.terraform_sa_email}"
}

# IAM bindings for App SA (Cloud SQL Client permissions)
resource "google_project_iam_member" "app_sa_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.app_sa_email}"
}

resource "google_project_iam_member" "app_sa_secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.app_sa_email}"
}

# IAM bindings for Cloud Function SAs (if provided)
resource "google_project_iam_member" "cf_sa_cloudsql_client" {
  for_each = toset(var.cloud_function_sa_emails)
  
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${each.value}"
}

resource "google_project_iam_member" "cf_sa_secretmanager_accessor" {
  for_each = toset(var.cloud_function_sa_emails)
  
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${each.value}"
}

# Secret access permissions for App SA
resource "google_secret_manager_secret_iam_member" "app_sa_db_url_access" {
  secret_id = google_secret_manager_secret.db_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.app_sa_email}"
  project   = var.project_id
}

resource "google_secret_manager_secret_iam_member" "app_sa_db_username_access" {
  secret_id = google_secret_manager_secret.db_username.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.app_sa_email}"
  project   = var.project_id
}

resource "google_secret_manager_secret_iam_member" "app_sa_db_password_access" {
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.app_sa_email}"
  project   = var.project_id
}

# Secret access permissions for Cloud Function SAs
resource "google_secret_manager_secret_iam_member" "cf_sa_db_url_access" {
  for_each = toset(var.cloud_function_sa_emails)
  
  secret_id = google_secret_manager_secret.db_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value}"
  project   = var.project_id
}

resource "google_secret_manager_secret_iam_member" "cf_sa_db_username_access" {
  for_each = toset(var.cloud_function_sa_emails)
  
  secret_id = google_secret_manager_secret.db_username.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value}"
  project   = var.project_id
}

resource "google_secret_manager_secret_iam_member" "cf_sa_db_password_access" {
  for_each = toset(var.cloud_function_sa_emails)
  
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value}"
  project   = var.project_id
}
