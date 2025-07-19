# Cloud SQL Module Outputs

# Instance information
output "instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "instance_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "instance_self_link" {
  description = "The self link of the Cloud SQL instance"
  value       = google_sql_database_instance.main.self_link
}

output "instance_service_account_email_address" {
  description = "The service account email address assigned to the instance"
  value       = google_sql_database_instance.main.service_account_email_address
}

# IP addresses
output "private_ip_address" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "public_ip_address" {
  description = "The public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

# Database information
output "database_name" {
  description = "The name of the main database"
  value       = google_sql_database.main_database.name
}

output "database_self_link" {
  description = "The self link of the main database"
  value       = google_sql_database.main_database.self_link
}

# User information
output "app_user_name" {
  description = "The name of the application database user"
  value       = google_sql_user.app_user.name
}

# Secret Manager information
output "db_name_secret_id" {
  description = "The secret ID for the database name"
  value       = google_secret_manager_secret.db_name.secret_id
}

output "db_name_secret_name" {
  description = "The full secret name for the database name"
  value       = google_secret_manager_secret.db_name.name
}

output "db_instance_connection_name_secret_id" {
  description = "The secret ID for the database instance connection name"
  value       = google_secret_manager_secret.db_instance_connection_name.secret_id
}

output "db_instance_connection_name_secret_name" {
  description = "The full secret name for the database instance connection name"
  value       = google_secret_manager_secret.db_instance_connection_name.name
}

output "db_username_secret_id" {
  description = "The secret ID for the database username"
  value       = google_secret_manager_secret.db_username.secret_id
}

output "db_username_secret_name" {
  description = "The full secret name for the database username"
  value       = google_secret_manager_secret.db_username.name
}

output "db_password_secret_id" {
  description = "The secret ID for the database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "db_password_secret_name" {
  description = "The full secret name for the database password"
  value       = google_secret_manager_secret.db_password.name
}

# Connection information for applications
output "connection_info" {
  description = "Database connection information for applications"
  value = {
    instance_connection_name = google_sql_database_instance.main.connection_name
    database_name           = google_sql_database.main_database.name
    private_ip_address      = google_sql_database_instance.main.private_ip_address
    public_ip_address       = google_sql_database_instance.main.public_ip_address
    app_user_name          = google_sql_user.app_user.name
  }
}

# Secret references for applications
output "secret_references" {
  description = "Secret Manager references for database credentials"
  value = {
    db_url_secret_name      = google_secret_manager_secret.db_url.name
    db_username_secret_name = google_secret_manager_secret.db_username.name
    db_password_secret_name = google_secret_manager_secret.db_password.name
  }
}
