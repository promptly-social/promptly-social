# GCP Resources, Secrets & Environment Variables Summary

## GCP Resources Created by Terraform

### Core Infrastructure

- **Cloud Run Service**: `promptly-backend-{environment}`
- **Cloud SQL Instance**: `promptly-db-{environment}` (PostgreSQL 15)
- **Cloud SQL Database**: `promptly_{environment}`
- **Cloud SQL User**: `promptly_user`
- **Artifact Registry Repository**: `promptly-backend`
- **Service Account**: `promptly-cloud-run-{environment}`

### Secret Manager Secrets

- `JWT_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GCP_ANALYSIS_FUNCTION_URL`

### APIs Enabled

- Cloud Run API (`run.googleapis.com`)
- Cloud SQL Admin API (`sqladmin.googleapis.com`)
- Secret Manager API (`secretmanager.googleapis.com`)
- Artifact Registry API (`artifactregistry.googleapis.com`)
- Cloud Build API (`cloudbuild.googleapis.com`)
- Identity and Access Management API (`iam.googleapis.com`)

## GitHub Secrets Required

### GCP Configuration

```
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
GCP_SA_KEY=<base64-encoded-service-account-key>
GCP_TERRAFORM_STATE_BUCKET=your-project-terraform-state
```

### Application Configuration

```
APP_NAME=promptly
FRONTEND_URL=https://your-frontend-domain.com
```

# Docker Hub no longer used - using Google Artifact Registry (configured by Terraform)

## Environment Variables (Auto-configured)

### Set by Terraform/Cloud Run

- `ENVIRONMENT`: staging/production
- `PORT`: 8000
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Set by Secret Manager

- `JWT_SECRET_KEY`: JWT signing key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Supabase service key
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `GCP_ANALYSIS_FUNCTION_URL`: Cloud function URL for analysis

## Service Account Permissions Required

The deployment service account needs these IAM roles:

- `roles/run.admin` - Cloud Run administration
- `roles/sql.admin` - Cloud SQL administration
- `roles/artifactregistry.admin` - Artifact Registry administration
- `roles/secretmanager.admin` - Secret Manager administration
- `roles/cloudbuild.builds.editor` - Cloud Build operations

## Quick Setup Commands

### 1. Create Service Account

```bash
gcloud iam service-accounts create promptly-deployer \
    --description="Service account for Promptly deployment" \
    --display-name="Promptly Deployer"
```

### 2. Grant Permissions

```bash
PROJECT_ID="your-project-id"
SA_EMAIL="promptly-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

for role in roles/run.admin roles/sql.admin roles/artifactregistry.admin roles/secretmanager.admin roles/cloudbuild.builds.editor; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role"
done
```

### 3. Create Terraform State Bucket

```bash
gsutil mb gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### 4. Create Service Account Key

```bash
gcloud iam service-accounts keys create key.json \
    --iam-account=promptly-deployer@${PROJECT_ID}.iam.gserviceaccount.com

# For GitHub Secret (base64 encode)
base64 -i key.json | pbcopy  # macOS
base64 -i key.json | xclip -selection clipboard  # Linux
```

## Resource Costs (Estimated Monthly)

### Staging Environment

- Cloud Run: $0-20 (depends on usage)
- Cloud SQL (db-f1-micro): $7-15
- Artifact Registry: $0.10/GB
- Secret Manager: $0.06/10k operations
- **Total: ~$10-40/month**

### Production Environment

- Cloud Run: $50-200 (depends on traffic)
- Cloud SQL (db-custom-2-4096): $100-150
- Artifact Registry: $0.10/GB
- Secret Manager: $0.06/10k operations
- **Total: ~$150-400/month**

## Deployment Checklist

### Pre-deployment

- [ ] GCP project created with billing enabled
- [ ] Service account created with proper permissions
- [ ] GitHub secrets configured
- [ ] Terraform state bucket created
- [ ] Domain/DNS configured (if needed)

### Infrastructure Deployment

- [ ] Run Terraform plan
- [ ] Apply Terraform configuration
- [ ] Verify resources created
- [ ] Update Secret Manager values

### Application Deployment

- [ ] Run GitHub Actions deployment workflow
- [ ] Verify Cloud Run service is running
- [ ] Test health endpoint
- [ ] Configure custom domain (if needed)

### Post-deployment

- [ ] Set up monitoring and alerting
- [ ] Configure backup retention
- [ ] Test disaster recovery procedures
- [ ] Document service URLs and access
