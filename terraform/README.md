# Terraform Infrastructure Documentation

This repository contains a refactored Terraform setup with clear separation between bootstrap (foundational) and infrastructure (application) resources.

## Architecture Overview

The Terraform configuration is split into two main modules:

1. **Bootstrap Module** (`terraform/modules/bootstrap/`) - Manages foundational resources
2. **Infrastructure Module** (`terraform/infrastructure/`) - Manages application resources

## Module Responsibilities

### Bootstrap Module
The bootstrap module handles foundational setup and should be applied **first** with organization owner credentials:

- **Service Accounts**: Creates Terraform SA and Application SA
- **IAM Roles**: Grants necessary permissions to service accounts
- **Workload Identity Federation**: Sets up GitHub Actions authentication
- **State Bucket**: Creates and manages Terraform state storage
- **Core APIs**: Enables foundational GCP APIs
- **DNS Permissions**: Manages DNS-related IAM bindings

**Key Resources:**
- `google_service_account.terraform_sa`
- `google_service_account.app_sa`
- `google_iam_workload_identity_pool.github_pool`
- `google_iam_workload_identity_pool_provider.github_provider`
- `google_storage_bucket.terraform_state`
- Core API enablement and IAM bindings

### Infrastructure Module
The infrastructure module handles application resources and should be applied **second** using the Terraform service account:

- **Application Resources**: Cloud Run, Secret Manager, Load Balancers
- **DNS Records**: Application-specific DNS entries
- **Storage**: Application data storage (GCS buckets)
- **Networking**: Load balancers, SSL certificates
- **Application APIs**: Enables application-specific GCP APIs

**Key Resources:**
- `google_cloud_run_service` (via module)
- `google_secret_manager_secret`
- `google_compute_*` (load balancer resources)
- `google_dns_record_set`
- `google_storage_bucket` (for frontend)

## Deployment Workflow

### 1. Bootstrap Deployment (One-time setup)
Apply the bootstrap module with organization owner credentials:

```bash
# Navigate to bootstrap environment
cd terraform/environments/bootstrap/production  # or staging

# Initialize and apply with org owner credentials
terraform init
terraform plan
terraform apply
```

### 2. Infrastructure Deployment (Regular deployments)
Apply the infrastructure module using the Terraform service account created by bootstrap:

```bash
# Navigate to infrastructure directory
cd terraform/infrastructure

# Configure to use Terraform SA for impersonation
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT="promptly-tf-sa-production@your-project.iam.gserviceaccount.com"

# Initialize and apply
terraform init
terraform plan
terraform apply
```

### 3. GitHub Actions Integration
GitHub Actions workflows authenticate using Workload Identity Federation:

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
    service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

- name: Deploy Infrastructure
  run: |
    cd terraform/infrastructure
    terraform init
    terraform plan
    terraform apply -auto-approve
```

## Authentication Flow

1. **Bootstrap Phase**: Organization owners apply bootstrap module directly
2. **Infrastructure Phase**: Terraform SA (created by bootstrap) applies infrastructure module
3. **GitHub Actions**: Uses WIF to authenticate as Terraform SA
4. **Runtime**: Application runs as Application SA with minimal required permissions

## Service Account Permissions

### Terraform Service Account
- Broad permissions for infrastructure management
- Can impersonate Application SA for deployments
- Used by GitHub Actions via WIF

### Application Service Account
- Runtime permissions only (Secret Manager, logging, etc.)
- Used by Cloud Run services
- Minimal required permissions following principle of least privilege

## Directory Structure

```
terraform/
├── modules/
│   └── bootstrap/           # Bootstrap module
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── infrastructure/          # Infrastructure module
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── environments/
│   └── bootstrap/
│       ├── production/      # Bootstrap for production
│       └── staging/         # Bootstrap for staging
├── examples/
│   └── integrated-deployment/  # Example of using both modules
└── README.md               # This file
```

## Key Benefits

1. **Clear Separation**: Bootstrap vs application concerns are clearly separated
2. **Security**: Principle of least privilege with proper service account roles
3. **Maintainability**: Each module has a single responsibility
4. **Scalability**: Easy to add new environments or applications
5. **CI/CD Ready**: Proper authentication flow for automated deployments

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you're using the correct service account for each phase
2. **Resource Conflicts**: Make sure bootstrap is applied before infrastructure
3. **WIF Authentication**: Verify GitHub repository and WIF provider configuration
4. **State Bucket Access**: Ensure Terraform SA has access to the state bucket

### Validation Commands

```bash
# Check service account impersonation
gcloud auth list

# Validate Terraform SA permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:*terraform-sa*"

# Test WIF authentication
gcloud iam workload-identity-pools describe github-pool-production --location=global
```

## Migration from Legacy Setup

If migrating from the previous monolithic setup:

1. Apply bootstrap module first
2. Import existing resources into appropriate modules
3. Remove conflicting resources from old configuration
4. Apply infrastructure module
5. Update CI/CD pipelines to use new authentication flow

## Security Considerations

- Bootstrap module requires organization owner permissions (one-time)
- Infrastructure deployments use service account impersonation
- Application runtime uses minimal permissions
- WIF provides secure GitHub Actions authentication without service account keys
- State bucket access is properly controlled

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review module documentation in respective directories
3. Validate authentication and permissions setup
4. Ensure proper deployment order (bootstrap → infrastructure)
