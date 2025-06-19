# Deployment Guide - Promptly Backend

This guide covers the complete CI/CD setup and deployment process for the Promptly backend to Google Cloud Platform (GCP), using secure, keyless authentication with Workload Identity Federation.

## Overview

The deployment setup includes:

- **Secure Keyless Authentication**: Using GCP's Workload Identity Federation to avoid long-lived service account keys.
- **GitHub Actions CI/CD pipelines** for automated testing and deployment
- **Terraform infrastructure** for GCP resource management (environment-specific)
- **Docker containerization** for consistent deployments
- **Google Cloud Run** for serverless deployment with anti-cold-start configuration
- **Supabase** for PostgreSQL database (external service)
- **Secret Manager** for secure application configuration management

## Table of Contents

- [Deployment Guide - Promptly Backend](#deployment-guide---promptly-backend)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [One-Time Manual Setup: Workload Identity Federation](#one-time-manual-setup-workload-identity-federation)
  - [GitHub Secrets Setup](#github-secrets-setup)
    - [Required Secrets](#required-secrets)
  - [Terraform Infrastructure](#terraform-infrastructure)
  - [CI/CD Pipelines](#cicd-pipelines)
  - [Deployment Process](#deployment-process)
  - [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
    - [Health Monitoring](#health-monitoring)
    - [Common Issues](#common-issues)
    - [Debugging Commands](#debugging-commands)
    - [Cost Optimization](#cost-optimization)
  - [Security Best Practices](#security-best-practices)
  - [Support and Maintenance](#support-and-maintenance)
    - [Regular Maintenance Tasks](#regular-maintenance-tasks)
    - [Getting Help](#getting-help)

## One-Time Manual Setup: Workload Identity Federation

To establish a secure, keyless connection between GitHub and GCP, you must perform a one-time bootstrap process. This is the most critical step for security.

Detailed instructions are in `terraform/bootstrap/README.md`. In summary:

1. **Authenticate locally** with a GCP user that has Owner permissions.
2. **Navigate** to the `terraform/bootstrap` directory.
3. **Create a `terraform.tfvars` file** with your `project_id` and `github_repo`.
4. **Run `terraform apply`** to create the Workload Identity Pool, Provider, and a dedicated service account for your Terraform CI/CD pipeline.

This process will output the values you need for your GitHub secrets.

## GitHub Secrets Setup

After completing the bootstrap process, you must configure the following secrets in your GitHub repository settings. **You will no longer use or need a service account JSON key.**

### Required Secrets

- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_WIF_PROVIDER`: The full resource name of the Workload Identity Provider created by the bootstrap process (e.g., `projects/123.../providers/github-provider`)
- `GCP_TERRAFORM_SA_EMAIL`: The email of the service account created for Terraform CI/CD (e.g., `promptly-terraform-sa@...`)
- `GCP_TERRAFORM_STATE_BUCKET`: The name of the GCS bucket for storing Terraform state
- `APP_NAME`: Application name (default: `promptly`)
- `FRONTEND_URL`: Your frontend domain URL

## Terraform Infrastructure

Your infrastructure is now managed entirely via the keyless CI/CD pipeline. The pipeline authenticates as the Terraform service account and then creates or updates your application's resources, including:

- A dedicated **Application Service Account** for Cloud Run in each environment
- IAM bindings that allow GitHub Actions to also impersonate the Application SA for deployments
- Cloud Run, Artifact Registry, Secret Manager, etc.

The configuration is organized by environment in `terraform/environments/`.

## CI/CD Pipelines

All pipelines now use `google-github-actions/auth@v2` for secure, keyless authentication.

- **Terraform Pipeline**: Authenticates as the **Terraform SA** (`GCP_TERRAFORM_SA_EMAIL`) to manage infrastructure
- **Backend Build/Deploy Pipelines**: Authenticate as the **Application SA** (e.g., `promptly-app-sa-production@...`) to push to Artifact Registry and deploy to Cloud Run. This follows the principle of least privilege.

## Deployment Process

The deployment process remains the same, but is now more secure.

1. **Initial Setup**: Complete the one-time manual bootstrap and set the required GitHub secrets
2. **Infrastructure**: Run the "Terraform Deploy Infrastructure" workflow to create your application's cloud resources
3. **Application**: Run the "Backend Deploy to GCP" workflow to deploy your application

## Monitoring and Troubleshooting

### Health Monitoring

- **Cloud Run Metrics**: Monitor in GCP Console
- **Application Logs**: View in Cloud Logging
- **Health Endpoint**: `https://your-service-url/health`
- **Metrics Endpoint**: `https://your-service-url/metrics`

### Common Issues

1. **Supabase Connection Issues**

   - Check Supabase project status
   - Verify SUPABASE_URL and keys in Secret Manager
   - Check network connectivity from Cloud Run

2. **Cold Start Issues (Production)**

   - Verify `cloud_run_min_instances = 1` in production
   - Check Cloud Run metrics for instance count
   - Monitor request latency

3. **Secret Manager Access**

   - Verify service account permissions
   - Check secret versions are latest
   - Validate secret names match

4. **Build Failures**

   - Check Docker build logs
   - Verify requirements.txt
   - Check Python version compatibility

### Debugging Commands

```bash
# View Cloud Run logs
gcloud logs read --service=promptly-backend-staging --limit=50

# Check service status and scaling
gcloud run services describe promptly-backend-production --region=us-central1

# Test health endpoint
curl -f https://your-service-url/health

# Check secret values (be careful with sensitive data)
gcloud secrets versions access latest --secret=SUPABASE_URL
```

### Cost Optimization

1. **Staging Environment**

   - Scales to zero when not used
   - Use for development and testing
   - Monitor usage patterns

2. **Production Environment**

   - Always-on instance prevents cold starts
   - Monitor concurrent requests
   - Adjust max instances based on traffic patterns

3. **General Optimization**

   - Regular dependency updates
   - Monitor Cloud Run metrics
   - Use committed use discounts for predictable workloads

## Security Best Practices

1. **Database Security (Supabase)**

   - Use Row Level Security (RLS) policies
   - Implement proper authentication flows
   - Monitor access patterns

2. **Secrets Management**

   - Never commit secrets to repository
   - Use Secret Manager for all sensitive data
   - Rotate secrets regularly (especially Supabase keys)

3. **IAM Configuration**

   - Follow principle of least privilege
   - Use service accounts for automation
   - Regular permission audits

4. **Container Security**
   - Regular base image updates
   - Security scanning in CI/CD
   - Non-root user in containers

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**

   - Review security scan results
   - Check application logs for errors
   - Monitor resource usage and scaling

2. **Monthly**

   - Update dependencies
   - Review and rotate secrets
   - Analyze cost reports
   - Review Supabase usage and performance

3. **Quarterly**
   - Security audit
   - Performance optimization review
   - Backup and disaster recovery testing

### Getting Help

- **GCP Documentation**: [Cloud Run](https://cloud.google.com/run/docs)
- **Supabase Documentation**: [Supabase Docs](https://supabase.com/docs)
- **GitHub Actions**: [Documentation](https://docs.github.com/en/actions)
- **Terraform**: [Google Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

---

This deployment setup provides a production-ready, scalable, and secure infrastructure for the Promptly backend application using Supabase as the database. The automated CI/CD pipelines ensure consistent deployments while maintaining high code quality and security standards. The environment-specific configuration allows for cost optimization in staging while ensuring zero cold starts in production.
