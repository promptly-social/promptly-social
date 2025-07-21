# User Activity Analysis Function Terraform Module

This Terraform module deploys a Google Cloud Function that analyzes user activity patterns on an hourly schedule. The function monitors user engagement through posts and conversations, triggering AI-powered analysis when activity thresholds are met.

## Features

- **Cloud Function**: Deploys a Python-based function for user activity analysis
- **Cloud Scheduler**: Configures hourly execution with comprehensive retry policies
- **Monitoring & Alerting**: Includes Cloud Monitoring alerts and custom metrics
- **Security**: Implements proper IAM roles and secret management
- **Operational Tools**: Provides management scripts for operational tasks

## Architecture

```
Cloud Scheduler → Cloud Function → Cloud SQL Database
                                ↓
                            AI Analysis Service
                                ↓
                        Cloud Monitoring & Logging
```

## Usage

### Basic Usage

```hcl
module "user_activity_analysis" {
  source = "./modules/user_activity_analysis_function"

  project_id            = "my-project"
  region               = "us-central1"
  service_account_email = "my-function-sa@my-project.iam.gserviceaccount.com"
  source_bucket        = "my-source-bucket"
  source_hash          = "abc123"
  function_source_dir  = "./src/gcp-functions"
}
```

### Advanced Configuration

```hcl
module "user_activity_analysis" {
  source = "./modules/user_activity_analysis_function"

  project_id            = "my-project"
  region               = "us-central1"
  service_account_email = "my-function-sa@my-project.iam.gserviceaccount.com"
  source_bucket        = "my-source-bucket"
  source_hash          = "abc123"
  function_source_dir  = "./src/gcp-functions"
  
  # Custom scheduling
  schedule             = "0 */2 * * *"  # Every 2 hours
  timezone            = "America/New_York"
  scheduler_paused    = false
  
  # Analysis configuration
  ai_provider         = "anthropic"
  post_threshold      = 3
  message_threshold   = 8
  batch_size         = 20
  
  # Monitoring configuration
  enable_monitoring_alerts    = true
  enable_custom_metrics       = true
  enable_monitoring_dashboard = true
  
  notification_channels = [
    "projects/my-project/notificationChannels/email-alerts",
    "projects/my-project/notificationChannels/slack-alerts"
  ]
  
  # Alert thresholds
  error_rate_threshold         = 0.1
  execution_time_threshold_ms  = 600000  # 10 minutes
  scheduler_failure_threshold  = 2
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| google | ~> 5.0 |
| google-beta | ~> 5.0 |
| archive | ~> 2.2.0 |
| null | ~> 3.1 |

## Providers

| Name | Version |
|------|---------|
| google | ~> 5.0 |
| google-beta | ~> 5.0 |
| archive | ~> 2.2.0 |

## Resources

### Core Resources
- `google_cloudfunctions2_function.function` - Main Cloud Function
- `google_cloud_scheduler_job.user_activity_analysis` - Scheduler job
- `google_storage_bucket_object.user_activity_analysis_source` - Function source code

### Monitoring Resources
- `google_monitoring_alert_policy.function_error_rate` - Function error alerts
- `google_monitoring_alert_policy.function_execution_time` - Execution time alerts
- `google_monitoring_alert_policy.scheduler_job_failures` - Scheduler failure alerts
- `google_logging_metric.analysis_completion_rate` - Custom completion metric
- `google_logging_metric.analysis_errors` - Custom error metric
- `google_monitoring_dashboard.user_activity_analysis` - System health dashboard

### Security Resources
- `google_secret_manager_secret_iam_member.*` - Secret access permissions
- `google_cloudfunctions2_function_iam_binding.user_activity_analysis_invoker` - Function invocation permissions

## Inputs

### Required Variables

| Name | Description | Type |
|------|-------------|------|
| project_id | The GCP project ID | `string` |
| service_account_email | Service account email for function execution | `string` |
| source_bucket | GCS bucket for storing function source code | `string` |
| source_hash | Hash of the source code for versioning | `string` |
| function_source_dir | The source directory of the function code | `string` |

### Optional Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| region | The GCP region for the function | `string` | `"us-central1"` |
| function_name | Name of the Cloud Function | `string` | `"user-activity-analysis"` |
| scheduler_job_name | Name of the Cloud Scheduler job | `string` | `"user-activity-analysis-trigger"` |
| schedule | Cron schedule for the analysis job | `string` | `"0 * * * *"` |
| timezone | Timezone for the scheduler | `string` | `"UTC"` |
| ai_provider | AI provider to use for analysis | `string` | `"openai"` |
| post_threshold | Minimum number of posts to trigger analysis | `number` | `5` |
| message_threshold | Minimum number of messages to trigger analysis | `number` | `10` |
| batch_size | Number of users to process in each batch | `number` | `10` |
| enable_monitoring_alerts | Enable Cloud Monitoring alert policies | `bool` | `true` |
| enable_custom_metrics | Enable custom logging metrics | `bool` | `true` |
| enable_monitoring_dashboard | Enable monitoring dashboard creation | `bool` | `true` |
| notification_channels | List of notification channel IDs for alerts | `list(string)` | `[]` |

## Outputs

| Name | Description |
|------|-------------|
| function_uri | The URI of the deployed Cloud Function |
| function_name | The name of the deployed Cloud Function |
| scheduler_job_name | The name of the Cloud Scheduler job |
| scheduler_job_id | The ID of the Cloud Scheduler job |
| monitoring_dashboard | The monitoring dashboard ID (if enabled) |
| alert_policy_function_errors | The function error rate alert policy (if enabled) |
| alert_policy_execution_time | The function execution time alert policy (if enabled) |
| alert_policy_scheduler_failures | The scheduler failure alert policy (if enabled) |

## Operational Management

### Scheduler Management Script

The module includes a management script for operational tasks:

```bash
# Set environment variables
export PROJECT_ID="my-project"
export REGION="us-central1"
export JOB_NAME="user-activity-analysis-trigger"

# Check job status
./scripts/manage_scheduler.sh status

# Pause the job
./scripts/manage_scheduler.sh pause

# Resume the job
./scripts/manage_scheduler.sh resume

# Trigger immediate execution
./scripts/manage_scheduler.sh run

# View logs
./scripts/manage_scheduler.sh logs 2  # Last 2 hours
./scripts/manage_scheduler.sh function-logs 6  # Last 6 hours

# Update schedule
./scripts/manage_scheduler.sh update-schedule "0 */2 * * *"
```

### Monitoring and Alerting

The module creates several monitoring resources:

1. **Alert Policies**:
   - Function error rate alerts
   - Function execution time alerts
   - Scheduler job failure alerts

2. **Custom Metrics**:
   - Analysis completion rate
   - Analysis error count

3. **Dashboard**:
   - Function execution metrics
   - Error rates and execution times
   - Scheduler job success rates

### Secret Management

The function requires access to these secrets:
- `CLOUD_SQL_INSTANCE_CONNECTION_NAME`
- `CLOUD_SQL_DATABASE_NAME`
- `CLOUD_SQL_USER`
- `CLOUD_SQL_PASSWORD`
- `OPENROUTER_API_KEY`

## Testing

The module includes comprehensive tests:

```bash
# Test basic functionality
terraform plan -var-file="test/terraform.tfvars" test/

# Test scheduler configuration
terraform plan -var-file="test/terraform.tfvars" test/scheduler_test.tf

# Test monitoring configuration
terraform plan -var-file="test/terraform.tfvars" test/monitoring_test.tf
```

## Security Considerations

- Function uses internal-only ingress settings
- Secrets are managed through Google Secret Manager
- IAM permissions follow principle of least privilege
- Service account has minimal required permissions

## Troubleshooting

### Common Issues

1. **Function timeout**: Increase `timeout_seconds` or optimize function code
2. **Scheduler failures**: Check retry configuration and function logs
3. **Permission errors**: Verify service account has required IAM roles
4. **Secret access**: Ensure secrets exist and have proper IAM bindings

### Debugging

```bash
# Check function logs
gcloud functions logs read user-activity-analysis --limit=50

# Check scheduler job status
gcloud scheduler jobs describe user-activity-analysis-trigger --location=us-central1

# View monitoring metrics
gcloud monitoring metrics list --filter="metric.type:custom.googleapis.com/user_activity_analysis"
```

## Contributing

When modifying this module:

1. Update variable descriptions and defaults
2. Add appropriate tests for new functionality
3. Update this README with new features
4. Ensure backward compatibility

## License

This module is part of the Promptly Social Scribe project.