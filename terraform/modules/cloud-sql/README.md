# Cloud SQL PostgreSQL Module

This Terraform module creates a secure Google Cloud SQL PostgreSQL instance with proper service account permissions, secret management, and environment-specific configurations.

## Features

- **Secure PostgreSQL Instance**: Creates a Cloud SQL PostgreSQL instance with security best practices
- **Private Networking**: Supports private IP configuration with VPC integration
- **Automated Backups**: Configurable backup schedules with point-in-time recovery
- **Secret Management**: Stores database credentials in Google Secret Manager
- **IAM Integration**: Creates IAM database users for service accounts
- **Multi-Environment Support**: Environment-specific naming and configurations
- **Monitoring**: Enables query insights and performance monitoring

## Usage

```hcl
module "cloud_sql" {
  source = "../modules/cloud-sql"
  
  # Required variables
  project_id          = var.project_id
  region             = var.region
  environment        = var.environment
  app_name           = var.app_name
  terraform_sa_email = var.terraform_sa_email
  app_sa_email       = var.app_sa_email
  
  # Instance configuration
  database_version = "POSTGRES_15"
  tier            = "db-f1-micro"
  disk_size       = 20
  disk_type       = "PD_SSD"
  
  # Security configuration
  require_ssl              = true
  deletion_protection      = true
  backup_enabled          = true
  point_in_time_recovery  = true
  
  # Network configuration
  private_network = var.vpc_network
  ipv4_enabled   = false
  
  # Cloud Function service accounts (optional)
  cloud_function_sa_emails = [
    "analyze-substack-sa@${var.project_id}.iam.gserviceaccount.com",
    "generate-suggestions-sa@${var.project_id}.iam.gserviceaccount.com"
  ]
}
```

## Environment-Specific Configurations

### Staging Environment
```hcl
module "cloud_sql" {
  source = "../modules/cloud-sql"
  
  # ... other variables ...
  
  # Cost-optimized settings for staging
  tier                = "db-f1-micro"
  disk_size          = 20
  availability_type  = "ZONAL"
  deletion_protection = false
  backup_retention_count = 3
}
```

### Production Environment
```hcl
module "cloud_sql" {
  source = "../modules/cloud-sql"
  
  # ... other variables ...
  
  # High-availability settings for production
  tier                = "db-n1-standard-2"
  disk_size          = 100
  availability_type  = "REGIONAL"
  deletion_protection = true
  backup_retention_count = 30
}
```

## Service Account Permissions

The module automatically configures the following IAM permissions:

### Terraform Service Account
- `roles/cloudsql.admin` - Full Cloud SQL instance management
- `roles/secretmanager.admin` - Secret creation and management

### Application Service Account
- `roles/cloudsql.client` - Database connection permissions
- `roles/secretmanager.secretAccessor` - Read database credentials

### Cloud Function Service Accounts
- `roles/cloudsql.client` - Database connection permissions
- `roles/secretmanager.secretAccessor` - Read database credentials

## Secret Manager Integration

The module creates the following secrets in Google Secret Manager:

- `${app_name}-${environment}-db-url` - Complete database connection URL
- `${app_name}-${environment}-db-username` - Database username
- `${app_name}-${environment}-db-password` - Database password

## Database Users

The module creates the following database users:

1. **Application User**: Standard PostgreSQL user with password authentication
2. **Terraform SA User**: IAM-based user for running migrations
3. **App SA User**: IAM-based user for application connections

## Security Features

- **SSL/TLS Encryption**: All connections require SSL
- **Private IP**: Instance uses private IP by default
- **Authorized Networks**: Configurable network access control
- **IAM Database Authentication**: Service accounts use IAM for database access
- **Secret Manager**: Database credentials stored securely
- **Audit Logging**: Database operations are logged for security monitoring

## Monitoring and Insights

- **Query Insights**: Enabled by default for performance monitoring
- **Application Tags**: Records application information in insights
- **Client Address**: Records client IP addresses for security auditing

## Backup Configuration

- **Automated Backups**: Daily backups with configurable retention
- **Point-in-Time Recovery**: Enabled for data recovery scenarios
- **Transaction Log Retention**: Configurable log retention period

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_id | The GCP project ID | `string` | n/a | yes |
| region | The GCP region for the Cloud SQL instance | `string` | n/a | yes |
| environment | Environment name (e.g., staging, production) | `string` | n/a | yes |
| app_name | Application name for resource naming | `string` | n/a | yes |
| terraform_sa_email | Email of the Terraform service account | `string` | n/a | yes |
| app_sa_email | Email of the application service account | `string` | n/a | yes |
| database_version | The PostgreSQL version to use | `string` | `"POSTGRES_15"` | no |
| tier | The machine type for the Cloud SQL instance | `string` | `"db-f1-micro"` | no |
| disk_size | The disk size in GB | `number` | `20` | no |
| disk_type | The disk type (PD_SSD or PD_HDD) | `string` | `"PD_SSD"` | no |
| deletion_protection | Enable deletion protection | `bool` | `true` | no |
| backup_enabled | Enable automated backups | `bool` | `true` | no |
| point_in_time_recovery | Enable point-in-time recovery | `bool` | `true` | no |
| private_network | VPC network for private IP | `string` | `null` | no |
| require_ssl | Require SSL connections | `bool` | `true` | no |
| cloud_function_sa_emails | List of Cloud Function service account emails | `list(string)` | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| instance_name | The name of the Cloud SQL instance |
| instance_connection_name | The connection name of the Cloud SQL instance |
| private_ip_address | The private IP address of the Cloud SQL instance |
| database_name | The name of the main database |
| connection_info | Database connection information for applications |
| secret_references | Secret Manager references for database credentials |

## Prerequisites

1. **VPC Network**: A VPC network must exist for private IP configuration
2. **Service Accounts**: Terraform SA and App SA must be created beforehand
3. **APIs**: The following APIs must be enabled:
   - Cloud SQL Admin API
   - Secret Manager API
   - Compute Engine API (for VPC)

## Migration Support

The module supports database migrations through the Terraform SA user, which has admin privileges. Applications can run migrations during startup using the App SA user.

## Cost Optimization

- Use `db-f1-micro` for development/staging environments
- Enable disk autoresize to avoid over-provisioning
- Use `ZONAL` availability for non-critical environments
- Adjust backup retention based on requirements

## Security Best Practices

- Always use private IP for production instances
- Enable deletion protection for production
- Use strong, randomly generated passwords
- Regularly rotate database credentials
- Monitor database access logs
- Use IAM database authentication where possible
