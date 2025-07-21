# User Activity Analysis Function Environments

This directory contains Terraform configurations for deploying the User Activity Analysis Cloud Function across different environments.

## Overview

The User Activity Analysis function analyzes user engagement patterns and runs **once daily at midnight PDT** (7 AM UTC) using Cloud Scheduler.

## Environments

### Staging (`staging/`)
- **Purpose**: Development and testing environment
- **Schedule**: Daily at midnight PDT (`0 7 * * *` in `America/Los_Angeles` timezone)
- **Configuration**: Lower thresholds and more lenient monitoring for testing
- **Service Account**: `promptly-app-sa-staging@{project_id}.iam.gserviceaccount.com`
- **Source Bucket**: `promptly-cf-source-staging`

### Production (`production/`)
- **Purpose**: Live production environment
- **Schedule**: Daily at midnight PDT (`0 7 * * *` in `America/Los_Angeles` timezone)
- **Configuration**: Production-ready thresholds and strict monitoring
- **Service Account**: `promptly-app-sa-production@{project_id}.iam.gserviceaccount.com`
- **Source Bucket**: `promptly-cf-source-production`

## Scheduler Configuration

Both environments are configured to run the analysis **once daily at midnight PDT**:
- **Cron Schedule**: `0 7 * * *` (7 AM UTC = midnight PDT during daylight saving time)
- **Timezone**: `America/Los_Angeles` (automatically handles PDT/PST transitions)
- **Retry Configuration**: Comprehensive retry logic with exponential backoff

## Key Features

### Analysis Configuration
- **OpenRouter Models**: Configurable primary and fallback AI models
- **Thresholds**: Minimum post/message counts to trigger analysis
- **Batch Processing**: Configurable batch sizes for user processing
- **Timeout**: 15-minute timeout for analysis operations

### Monitoring & Alerting
- **Cloud Monitoring**: Function execution metrics and alerts
- **Custom Metrics**: Analysis completion rates and error tracking
- **Scheduler Monitoring**: Pub/Sub-based scheduler job monitoring
- **Dashboard**: Comprehensive system health dashboard

### Security
- **Service Account**: Dedicated service accounts per environment
- **Secret Manager**: Secure storage for database credentials and API keys
- **IAM**: Least-privilege access controls

## Deployment

### Prerequisites
1. Ensure the required service accounts exist
2. Verify source buckets are created
3. Confirm Secret Manager secrets are configured

### Deploy Staging
```bash
cd terraform/environments/user_activity_analysis/staging
terraform init
terraform plan
terraform apply
```

### Deploy Production
```bash
cd terraform/environments/user_activity_analysis/production
terraform init
terraform plan
terraform apply
```

## Configuration Variables

### Staging-Specific
- `post_threshold`: 3 (lower for testing)
- `message_threshold`: 5 (lower for testing)
- `batch_size`: 5 (smaller batches)
- More lenient alert thresholds

### Production-Specific
- `post_threshold`: 5 (production standard)
- `message_threshold`: 10 (production standard)
- `batch_size`: 10 (larger batches)
- Strict alert thresholds

## Monitoring

Each environment includes:
- Function error rate alerts
- Execution time monitoring
- Scheduler job failure alerts
- Custom metrics for analysis completion
- System health dashboard

## Troubleshooting

### Scheduler Issues
- Check Cloud Scheduler console for job status
- Review function logs in Cloud Logging
- Verify service account permissions

### Function Errors
- Monitor the system health dashboard
- Check alert policies for notifications
- Review custom metrics for analysis patterns

## Related Documentation
- [User Activity Analysis Module](../../modules/user_activity_analysis_function/README.md)
- [Function Source Code](../../src/gcp-functions/user_activity_analysis/)
