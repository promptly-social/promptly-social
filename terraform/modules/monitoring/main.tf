terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Notification channels for alerts
resource "google_monitoring_notification_channel" "email" {
  count = length(var.notification_emails)
  
  display_name = "Email - ${var.notification_emails[count.index]}"
  type         = "email"
  
  labels = {
    email_address = var.notification_emails[count.index]
  }
  
  enabled = true
}

# Notification channels for Slack (if configured)
resource "google_monitoring_notification_channel" "slack" {
  count = var.slack_webhook_url != "" ? 1 : 0
  
  display_name = "Slack - ${var.app_name}-${var.environment}"
  type         = "slack"
  
  labels = {
    url = var.slack_webhook_url
  }
  
  enabled = true
}

# Cloud Function monitoring alerts
resource "google_monitoring_alert_policy" "cloud_function_errors" {
  count = var.enable_cloud_function_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud Function Error Rate"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud Functions have high error rates"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud Function Error Rate"
    
    condition_threshold {
      filter = "resource.type=\"cloud_function\" resource.label.project_id=\"${var.project_id}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" metric.label.status!=\"ok\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_function_error_threshold
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

resource "google_monitoring_alert_policy" "cloud_function_execution_time" {
  count = var.enable_cloud_function_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud Function Execution Time"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud Functions execution time exceeds threshold"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud Function Execution Time"
    
    condition_threshold {
      filter = "resource.type=\"cloud_function\" resource.label.project_id=\"${var.project_id}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_times\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_function_execution_time_threshold_ms
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

# Cloud Run monitoring alerts
resource "google_monitoring_alert_policy" "cloud_run_errors" {
  count = var.enable_cloud_run_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud Run Error Rate"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud Run services have high error rates"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud Run Error Rate"
    
    condition_threshold {
      filter = "resource.type=\"cloud_run_revision\" resource.label.project_id=\"${var.project_id}\" metric.type=\"run.googleapis.com/request_count\" metric.label.response_code_class!=\"2xx\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_run_error_threshold
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

resource "google_monitoring_alert_policy" "cloud_run_latency" {
  count = var.enable_cloud_run_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud Run High Latency"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud Run services have high latency"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud Run High Latency"
    
    condition_threshold {
      filter = "resource.type=\"cloud_run_revision\" resource.label.project_id=\"${var.project_id}\" metric.type=\"run.googleapis.com/request_latencies\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_run_latency_threshold_ms
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

# Cloud SQL monitoring alerts
resource "google_monitoring_alert_policy" "cloud_sql_cpu" {
  count = var.enable_cloud_sql_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud SQL High CPU"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud SQL CPU utilization is high"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud SQL High CPU"
    
    condition_threshold {
      filter = "resource.type=\"cloudsql_database\" resource.label.project_id=\"${var.project_id}\" metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_sql_cpu_threshold
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

resource "google_monitoring_alert_policy" "cloud_sql_memory" {
  count = var.enable_cloud_sql_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud SQL High Memory"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud SQL memory utilization is high"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud SQL High Memory"
    
    condition_threshold {
      filter = "resource.type=\"cloudsql_database\" resource.label.project_id=\"${var.project_id}\" metric.type=\"cloudsql.googleapis.com/database/memory/utilization\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_sql_memory_threshold
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

resource "google_monitoring_alert_policy" "cloud_sql_connections" {
  count = var.enable_cloud_sql_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud SQL High Connections"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud SQL has too many connections"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud SQL High Connections"
    
    condition_threshold {
      filter = "resource.type=\"cloudsql_database\" resource.label.project_id=\"${var.project_id}\" metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_sql_connections_threshold
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

# Cloud Scheduler monitoring alerts
resource "google_monitoring_alert_policy" "cloud_scheduler_failures" {
  count = var.enable_cloud_scheduler_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Cloud Scheduler Job Failures"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Cloud Scheduler jobs fail repeatedly"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Cloud Scheduler Job Failures"
    
    condition_threshold {
      filter = "resource.type=\"cloud_scheduler_job\" resource.label.project_id=\"${var.project_id}\" metric.type=\"cloudscheduler.googleapis.com/job/num_attempts\" metric.label.response_code!=\"200\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.cloud_scheduler_failure_threshold
      duration        = "600s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "3600s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

# Load Balancer monitoring alerts
resource "google_monitoring_alert_policy" "load_balancer_errors" {
  count = var.enable_load_balancer_monitoring ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Load Balancer Error Rate"
  project      = var.project_id
  
  documentation {
    content   = "Alert when Load Balancer has high error rates"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Load Balancer Error Rate"
    
    condition_threshold {
      filter = "resource.type=\"https_lb_rule\" resource.label.project_id=\"${var.project_id}\" metric.type=\"loadbalancing.googleapis.com/https/request_count\" metric.label.response_code!~\"2..\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = var.load_balancer_error_threshold
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}

# Custom logging metrics for application-specific monitoring
resource "google_logging_metric" "application_errors" {
  count = var.enable_custom_metrics ? 1 : 0
  
  name    = "${var.app_name}_${var.environment}_application_errors"
  project = var.project_id
  
  filter = <<-EOT
    (resource.type="cloud_function" OR resource.type="cloud_run_revision")
    resource.label.project_id="${var.project_id}"
    (severity>=ERROR OR jsonPayload.level="ERROR")
  EOT
  
  metric_descriptor {
    metric_kind  = "CUMULATIVE"
    value_type   = "INT64"
    display_name = "${var.app_name} ${var.environment} Application Errors"
  }
  
  label_extractors = {
    service_name = "EXTRACT(resource.labels.service_name)"
    error_type   = "EXTRACT(jsonPayload.error_type)"
    environment  = "\"${var.environment}\""
  }
}

resource "google_logging_metric" "user_activity_analysis_completion" {
  count = var.enable_custom_metrics ? 1 : 0
  
  name    = "${var.app_name}_${var.environment}_user_activity_analysis_completion"
  project = var.project_id
  
  filter = <<-EOT
    resource.type="cloud_function"
    resource.label.project_id="${var.project_id}"
    jsonPayload.message="Analysis completed successfully"
  EOT
  
  metric_descriptor {
    metric_kind  = "GAUGE"
    value_type   = "INT64"
    display_name = "${var.app_name} ${var.environment} User Activity Analysis Completion"
  }
  
  value_extractor = "EXTRACT(jsonPayload.users_processed)"
  
  label_extractors = {
    function_name = "EXTRACT(resource.labels.function_name)"
    batch_size    = "EXTRACT(jsonPayload.batch_size)"
    environment   = "\"${var.environment}\""
  }
}

# Uptime checks for critical endpoints
resource "google_monitoring_uptime_check_config" "api_uptime" {
  count = var.enable_uptime_checks && var.api_endpoint != "" ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} API Uptime"
  timeout      = "10s"
  period       = "300s"
  
  http_check {
    path         = var.api_health_check_path
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.api_endpoint
    }
  }
  
  content_matchers {
    content = var.api_health_check_response
    matcher = "CONTAINS_STRING"
  }
}

resource "google_monitoring_uptime_check_config" "frontend_uptime" {
  count = var.enable_uptime_checks && var.frontend_endpoint != "" ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} Frontend Uptime"
  timeout      = "10s"
  period       = "300s"
  
  http_check {
    path         = "/"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.frontend_endpoint
    }
  }
  
  content_matchers {
    content = "<title>"
    matcher = "CONTAINS_STRING"
  }
}

# Uptime check alerts
resource "google_monitoring_alert_policy" "uptime_check_failures" {
  count = var.enable_uptime_checks ? 1 : 0
  
  display_name = "${var.app_name}-${var.environment} - Uptime Check Failures"
  project      = var.project_id
  
  documentation {
    content   = "Alert when uptime checks fail"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Uptime Check Failures"
    
    condition_threshold {
      filter = "resource.type=\"uptime_url\" resource.label.project_id=\"${var.project_id}\" metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\""
      
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "300s"
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_FRACTION_TRUE"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  combiner              = "OR"
  enabled               = true
  notification_channels = concat(
    google_monitoring_notification_channel.email[*].id,
    google_monitoring_notification_channel.slack[*].id
  )
}
