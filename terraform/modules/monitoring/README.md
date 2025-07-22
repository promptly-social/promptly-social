# Monitoring Module

This Terraform module provides comprehensive monitoring, alerting, and dashboards for GCP resources including Cloud Functions, Cloud Run, Cloud SQL, Cloud Scheduler, and Load Balancers.

## Features

- **Multi-service Monitoring**: Monitors Cloud Functions, Cloud Run, Cloud SQL, Cloud Scheduler, and Load Balancers
- **Comprehensive Alerting**: Error rates, latency, resource utilization, and uptime alerts
- **Custom Dashboards**: Pre-built dashboards for system overview and service-specific metrics
- **Flexible Notifications**: Email and Slack notification channels
- **Uptime Checks**: HTTP/HTTPS uptime monitoring for critical endpoints
- **Custom Metrics**: Application-specific logging metrics
- **Multi-environment Support**: Environment-specific configurations and naming

## Usage

```hcl
module "monitoring" {
  source = "../modules/monitoring"
  
  # Required variables
  project_id  = var.project_id
  app_name    = var.app_name
  environment = var.environment
  
  # Notification configuration
  notification_emails = ["admin@example.com", "devops@example.com"]
  slack_webhook_url   = var.slack_webhook_url  # Optional
  
  # Feature toggles
  enable_cloud_function_monitoring  = true
  enable_cloud_run_monitoring      = true
  enable_cloud_sql_monitoring      = true
  enable_cloud_scheduler_monitoring = true
  enable_load_balancer_monitoring  = true
  enable_uptime_checks             = true
  enable_custom_metrics            = true
  enable_dashboards                = true
  
  # Uptime check endpoints
  api_endpoint      = "api.example.com"
  frontend_endpoint = "example.com"
  
  # Custom thresholds (optional)
  cloud_function_error_threshold = 0.1
  cloud_run_error_threshold     = 1.0
  cloud_sql_cpu_threshold       = 0.8
}
```

## Resources Created

### Notification Channels
- Email notification channels for each provided email address
- Slack notification channel (if webhook URL provided)

### Alert Policies
- **Cloud Functions**: Error rate and execution time alerts
- **Cloud Run**: Error rate and latency alerts
- **Cloud SQL**: CPU, memory, and connection alerts
- **Cloud Scheduler**: Job failure alerts
- **Load Balancer**: Error rate alerts
- **Uptime Checks**: Endpoint availability alerts

### Custom Metrics
- Application error tracking across services
- User activity analysis completion metrics

### Dashboards
- **System Overview**: High-level view of all services
- **Cloud Functions**: Function-specific metrics and performance
- **Cloud Run**: Service metrics, CPU, and memory utilization
- **Cloud SQL**: Database performance and resource usage

### Uptime Checks
- API endpoint health monitoring
- Frontend application availability

## Variables

| Variable | Description | Type | Default |
|----------|-------------|------|---------|
| `project_id` | GCP project ID | `string` | Required |
| `app_name` | Application name | `string` | Required |
| `environment` | Deployment environment | `string` | Required |
| `notification_emails` | Email addresses for alerts | `list(string)` | `[]` |
| `slack_webhook_url` | Slack webhook URL | `string` | `""` |
| `enable_cloud_function_monitoring` | Enable Cloud Function monitoring | `bool` | `true` |
| `enable_cloud_run_monitoring` | Enable Cloud Run monitoring | `bool` | `true` |
| `enable_cloud_sql_monitoring` | Enable Cloud SQL monitoring | `bool` | `true` |
| `enable_cloud_scheduler_monitoring` | Enable Cloud Scheduler monitoring | `bool` | `true` |
| `enable_load_balancer_monitoring` | Enable Load Balancer monitoring | `bool` | `true` |
| `enable_uptime_checks` | Enable uptime checks | `bool` | `true` |
| `enable_custom_metrics` | Enable custom metrics | `bool` | `true` |
| `enable_dashboards` | Enable dashboards | `bool` | `true` |

### Threshold Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `cloud_function_error_threshold` | Function error rate (errors/sec) | `0.1` |
| `cloud_function_execution_time_threshold_ms` | Function timeout (ms) | `600000` |
| `cloud_run_error_threshold` | Cloud Run error rate (errors/sec) | `1.0` |
| `cloud_run_latency_threshold_ms` | Cloud Run latency (ms) | `5000` |
| `cloud_sql_cpu_threshold` | SQL CPU utilization (%) | `0.8` |
| `cloud_sql_memory_threshold` | SQL memory utilization (%) | `0.9` |
| `cloud_sql_connections_threshold` | SQL connection count | `80` |

## Outputs

The module provides comprehensive outputs for integration with other modules:

- `all_notification_channels`: All notification channel IDs
- `cloud_function_alert_policies`: Cloud Function alert policy names
- `cloud_run_alert_policies`: Cloud Run alert policy names
- `cloud_sql_alert_policies`: Cloud SQL alert policy names
- `dashboards`: Dashboard IDs
- `monitoring_summary`: Summary of created resources

## Prerequisites

### Required GCP APIs
The following APIs must be enabled in your project:
- `monitoring.googleapis.com`
- `logging.googleapis.com`

### IAM Permissions
The Terraform service account needs the following roles:
- `roles/monitoring.editor`
- `roles/logging.configWriter`

## Best Practices

1. **Environment-specific Configuration**: Use different thresholds for staging vs production
2. **Notification Management**: Use separate notification channels for different severity levels
3. **Dashboard Customization**: Modify dashboard configurations based on your specific needs
4. **Alert Tuning**: Start with default thresholds and adjust based on your application behavior
5. **Resource Labeling**: Ensure consistent labeling across resources for better filtering

## Integration with Infrastructure

This module is designed to be used alongside your main infrastructure module:

```hcl
# In your main infrastructure
module "monitoring" {
  source = "../modules/monitoring"
  
  project_id  = var.project_id
  app_name    = var.app_name
  environment = var.environment
  
  notification_emails = var.monitoring_emails
  
  # Enable monitoring for deployed services
  enable_cloud_function_monitoring = var.manage_cloud_functions
  enable_cloud_run_monitoring     = var.manage_cloud_run_service
  enable_cloud_sql_monitoring     = var.manage_cloud_sql
  
  depends_on = [
    module.cloud_run_service,
    module.cloud_sql,
    # other service modules
  ]
}
```

## Troubleshooting

### Common Issues

1. **Missing APIs**: Ensure monitoring and logging APIs are enabled
2. **Permission Errors**: Verify Terraform SA has monitoring.editor role
3. **Alert Noise**: Adjust thresholds if receiving too many false positives
4. **Dashboard Empty**: Check that resources are properly labeled and generating metrics

### Debugging

- Use `gcloud logging read` to verify log-based metrics are working
- Check Cloud Monitoring console to verify alert policies are active
- Test notification channels manually from the GCP console
