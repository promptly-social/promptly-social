# Docker Registry Migration - Docker Hub to Google Artifact Registry

## Summary of Changes

We have successfully migrated from Docker Hub to Google Artifact Registry (GAR) for private container storage. This provides better integration with GCP services and enhanced security.

## What Changed

### ✅ Terraform Infrastructure

- **Artifact Registry Repository**: Already configured in `terraform/main.tf`
- **IAM Permissions**: Service account has `roles/artifactregistry.admin`
- **Repository URL**: `{region}-docker.pkg.dev/{project-id}/promptly-backend/backend`

### ✅ GitHub Actions Workflows

- **Main Branch Workflow** (`.github/workflows/backend-main.yml`):

  - Removed Docker Hub authentication
  - Added GCP authentication and gcloud docker configuration
  - Updated image URL to use Artifact Registry
  - Images pushed to: `{region}-docker.pkg.dev/{project-id}/promptly-backend/backend:{tag}`

- **Deployment Workflow** (`.github/workflows/backend-deploy.yml`):

  - Already using Artifact Registry (no changes needed)

- **PR Workflow** (`.github/workflows/backend-pr.yml`):
  - Removed PostgreSQL service (using Supabase)
  - No Docker Hub dependencies

### ✅ Environment Configuration

- **Environment-Specific Setup**:
  - Staging: `cloud_run_min_instances = 0` (cost optimization)
  - Production: `cloud_run_min_instances = 1` (anti-cold-start)

### ✅ Documentation Updates

- **DEPLOYMENT.md**: Removed Docker Hub references
- **RESOURCES_SUMMARY.md**: Updated to reflect GAR usage
- **Cost Estimates**: Updated without CloudSQL costs

## Required GitHub Secrets

### Required (Existing)

- ✅ `GCP_PROJECT_ID`
- ✅ `GCP_REGION`
- ✅ `GCP_SA_KEY`
- ✅ `GCP_TERRAFORM_STATE_BUCKET`

## Benefits of Migration

### 🔒 Enhanced Security

- **Private Registry**: Images are not publicly accessible
- **IAM Integration**: Fine-grained access control using GCP IAM
- **VPC-Native**: Images stay within your GCP environment

### 💰 Cost Optimization

- **No External Registry Costs**: Included in GCP usage
- **Data Transfer**: No egress charges for images pulled within same region
- **Storage Efficiency**: Automatic layer deduplication

### 🚀 Performance Improvements

- **Regional Storage**: Faster image pulls within GCP
- **Integrated CDN**: Global distribution with Cloud CDN
- **Concurrent Pulls**: Better performance for scaling events

### 🛠️ Better DevOps Integration

- **Native GCP Integration**: Works seamlessly with Cloud Run
- **Vulnerability Scanning**: Built-in container scanning
- **Audit Logs**: Complete image access logging

## Image Management

### Image URLs

```
# Staging
us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend:staging

# Production
us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend:latest
us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend:main-{commit-hash}
```

### Local Development

To pull images locally for debugging:

```bash
# Authenticate Docker with GCP
gcloud auth configure-docker us-central1-docker.pkg.dev

# Pull image
docker pull us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend:latest
```

### Image Cleanup

Artifact Registry automatically manages old images, but you can set up lifecycle policies:

```bash
# List images
gcloud artifacts docker images list us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend

# Delete specific image
gcloud artifacts docker images delete us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend:old-tag
```

## Anti-Cold Start Configuration

### Production Environment

- **Minimum Instances**: 1 (always warm)
- **Cost Impact**: ~$30-50/month for always-on instance
- **User Experience**: Zero cold start delays

### Staging Environment

- **Minimum Instances**: 0 (scales to zero)
- **Cost Impact**: ~$0-20/month when not in use
- **User Experience**: May have cold starts after inactivity

## Deployment Process

### Automatic (Main Branch)

1. Code merged to `main`
2. Tests run automatically
3. Docker image built and pushed to GAR
4. Image tagged with commit hash and `latest`

### Manual (Environment Deployment)

1. Trigger "Backend Deploy to GCP" workflow
2. Select environment (staging/production)
3. Specify tag or use latest from main
4. Deploy with environment-specific scaling

### Infrastructure Updates

1. Trigger "Terraform Deploy Infrastructure"
2. Select environment and action (plan/apply)
3. Terraform manages GAR repository and permissions

## Monitoring and Troubleshooting

### Registry Access

```bash
# Check repository access
gcloud artifacts repositories describe promptly-backend \
    --location=us-central1

# List images
gcloud artifacts docker images list \
    us-central1-docker.pkg.dev/{project-id}/promptly-backend/backend \
    --include-tags

# Check IAM permissions
gcloud artifacts repositories get-iam-policy promptly-backend \
    --location=us-central1
```

### Common Issues

**Authentication Errors**:

```bash
# Re-authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Check service account permissions
gcloud projects get-iam-policy {project-id} \
    --filter="bindings.members:serviceAccount:*@{project-id}.iam.gserviceaccount.com"
```

**Build Failures**:

- Check GitHub Actions logs for authentication issues
- Verify GCP_SA_KEY secret is correctly base64 encoded
- Ensure service account has `roles/artifactregistry.admin`

**Pull Errors in Cloud Run**:

- Verify image exists in registry
- Check Cloud Run service account permissions
- Ensure image URL format is correct

## Next Steps

1. **Monitor Costs**: Review GCP billing for Artifact Registry usage
2. **Set Up Scanning**: Enable vulnerability scanning for images
3. **Lifecycle Policies**: Configure automatic cleanup of old images
4. **Access Control**: Review and refine IAM permissions as needed

This migration provides a more secure, cost-effective, and performant container registry solution fully integrated with your GCP infrastructure.
