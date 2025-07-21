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
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Storage bucket object for function source code
resource "google_storage_bucket_object" "user_activity_analysis_source" {
  name   = "user-activity-analysis-${var.source_hash}.zip"
  bucket = var.source_bucket
  source = data.archive_file.user_activity_analysis_source.output_path
}

# Archive the function source code
data "archive_file" "user_activity_analysis_source" {
  type        = "zip"
  source_dir  = var.function_source_dir
  output_path = "/tmp/user-activity-analysis-${var.source_hash}.zip"
  excludes = [
    "terraform/**",
    "README.md",
    "env.example",
    ".env",
    "test**",
    "test-output.json",
    "venv/**",
    "__pycache__/**",
    ".pytest_cache/**",
    "htmlcov/**",
    "analyze/**",
    "generate_suggestions/**",
    "unified_post_scheduler/**",
    "user_activity_analysis/venv/**",
    "user_activity_analysis/__pycache__/**",
    "user_activity_analysis/.pytest_cache/**",
    "user_activity_analysis/htmlcov/**",
    "user_activity_analysis/test**"
  ]
}

# Cloud Function resource
resource "google_cloudfunctions2_function" "function" {
  name        = var.function_name
  location    = var.region
  project     = var.project_id
  description = "User activity analysis function that runs hourly to analyze user engagement patterns"

  build_config {
    runtime     = "python313"
    entry_point = "analyze_user_activity"
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.user_activity_analysis_source.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "1Gi"
    timeout_seconds    = 900  # 15 minutes as per requirements
    
    environment_variables = {
      AI_PROVIDER                = var.ai_provider
      POST_THRESHOLD             = var.post_threshold
      MESSAGE_THRESHOLD          = var.message_threshold
      MAX_RETRY_ATTEMPTS         = var.max_retry_attempts
      ANALYSIS_TIMEOUT_MINUTES   = var.analysis_timeout_minutes
      BATCH_SIZE                 = var.batch_size
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
      project_id = var.project_id
      secret     = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_DATABASE_NAME"
      project_id = var.project_id
      secret     = "CLOUD_SQL_DATABASE_NAME"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_USER"
      project_id = var.project_id
      secret     = "CLOUD_SQL_USER"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "CLOUD_SQL_PASSWORD"
      project_id = var.project_id
      secret     = "CLOUD_SQL_PASSWORD"
      version    = "latest"
    }

    secret_environment_variables {
      key        = "OPENROUTER_API_KEY"
      project_id = var.project_id
      secret     = "OPENROUTER_API_KEY"
      version    = "latest"
    }

    ingress_settings = "ALLOW_INTERNAL_ONLY"
    
    service_account_email = var.service_account_email
  }

  depends_on = [
    google_storage_bucket_object.user_activity_analysis_source,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_instance_connection_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_database_name,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_user,
    google_secret_manager_secret_iam_member.secret_access_cloud_sql_password,
    google_secret_manager_secret_iam_member.secret_access_openrouter_key,
  ]
}

# Cloud Scheduler job to trigger the function every hour
resource "google_cloud_scheduler_job" "user_activity_analysis" {
  project          = var.project_id
  region           = var.region
  name             = var.scheduler_job_name
  description      = "Triggers user activity analysis function every hour with comprehensive retry and monitoring"
  schedule         = var.schedule
  time_zone        = var.timezone
  attempt_deadline = "900s"  # 15 minutes as per requirements
  paused           = var.scheduler_paused

  retry_config {
    retry_count          = var.scheduler_retry_count
    max_retry_duration   = var.scheduler_max_retry_duration
    min_backoff_duration = var.scheduler_min_backoff_duration
    max_backoff_duration = var.scheduler_max_backoff_duration
    max_doublings        = var.scheduler_max_doublings
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.function.service_config[0].uri
    
    headers = {
      "Content-Type" = "application/json"
      "X-Scheduler-Job" = var.scheduler_job_name
      "X-Environment" = var.environment
    }
    
    # Include metadata in the request body for better tracking
    body = base64encode(jsonencode({
      scheduler_job_name = var.scheduler_job_name
      environment       = var.environment
      triggered_at      = "{{.ScheduleTime}}"
      attempt_number    = "{{.AttemptNumber}}"
    }))

    oidc_token {
      service_account_email = var.service_account_email
      audience             = google_cloudfunctions2_function.function.service_config[0].uri
    }
  }

  depends_on = [
    google_cloudfunctions2_function.function
  ]
}

# Create a log sink for scheduler job monitoring
resource "google_logging_project_sink" "scheduler_monitoring" {
  count = var.enable_scheduler_monitoring ? 1 : 0
  
  name        = "${var.scheduler_job_name}-monitoring-sink"
  destination = "pubsub.googleapis.com/projects/${var.project_id}/topics/${google_pubsub_topic.scheduler_monitoring[0].name}"
  
  filter = <<-EOT
    resource.type="cloud_scheduler_job"
    resource.labels.job_id="${var.scheduler_job_name}"
    resource.labels.location="${var.region}"
    (severity>=ERROR OR jsonPayload.status="FAILED")
  EOT

  unique_writer_identity = true
}

# Pub/Sub topic for scheduler monitoring
resource "google_pubsub_topic" "scheduler_monitoring" {
  count = var.enable_scheduler_monitoring ? 1 : 0
  
  name    = "${var.scheduler_job_name}-monitoring"
  project = var.project_id
  
  labels = {
    environment = var.environment
    component   = "scheduler-monitoring"
    function    = var.function_name
  }
}

# Grant the log sink permission to publish to the topic
resource "google_pubsub_topic_iam_member" "scheduler_monitoring_publisher" {
  count = var.enable_scheduler_monitoring ? 1 : 0
  
  topic   = google_pubsub_topic.scheduler_monitoring[0].name
  role    = "roles/pubsub.publisher"
  member  = google_logging_project_sink.scheduler_monitoring[0].writer_identity
  project = var.project_id
}

# Cloud Monitoring Alert Policy for Function Errors
resource "google_monitoring_alert_policy" "function_error_rate" {
  count = var.enable_monitoring_alerts ? 1 : 0
  
  display_name = "${var.function_name} Error Rate Alert"
  project      = var.project_id
  
  documentation {
    content = "Alert when the user activity analysis function has a high error rate"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Function Error Rate"
    
    condition_threshold {
      filter = "resource.type=\"cloud_function\" resource.label.function_name=\"${var.function_name}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" metric.label.status!=\"ok\""
      
      comparison = "COMPARISON_GREATER_THAN"
      threshold_value = var.error_rate_threshold
      duration = "300s"  # 5 minutes
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"  # 30 minutes
  }

  combiner = "OR"
  enabled  = true

  dynamic "notification_channels" {
    for_each = var.notification_channels
    content {
      notification_channels = [notification_channels.value]
    }
  }
}

# Cloud Monitoring Alert Policy for Function Execution Time
resource "google_monitoring_alert_policy" "function_execution_time" {
  count = var.enable_monitoring_alerts ? 1 : 0
  
  display_name = "${var.function_name} Execution Time Alert"
  project      = var.project_id
  
  documentation {
    content = "Alert when the user activity analysis function execution time exceeds threshold"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Function Execution Time"
    
    condition_threshold {
      filter = "resource.type=\"cloud_function\" resource.label.function_name=\"${var.function_name}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_times\""
      
      comparison = "COMPARISON_GREATER_THAN"
      threshold_value = var.execution_time_threshold_ms
      duration = "300s"  # 5 minutes
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"  # 30 minutes
  }

  combiner = "OR"
  enabled  = true

  dynamic "notification_channels" {
    for_each = var.notification_channels
    content {
      notification_channels = [notification_channels.value]
    }
  }
}

# Cloud Monitoring Alert Policy for Scheduler Job Failures
resource "google_monitoring_alert_policy" "scheduler_job_failures" {
  count = var.enable_monitoring_alerts ? 1 : 0
  
  display_name = "${var.scheduler_job_name} Failure Alert"
  project      = var.project_id
  
  documentation {
    content = "Alert when the scheduler job fails repeatedly"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Scheduler Job Failures"
    
    condition_threshold {
      filter = "resource.type=\"cloud_scheduler_job\" resource.label.job_id=\"${var.scheduler_job_name}\" metric.type=\"cloudscheduler.googleapis.com/job/num_attempts\" metric.label.response_code!=\"200\""
      
      comparison = "COMPARISON_GREATER_THAN"
      threshold_value = var.scheduler_failure_threshold
      duration = "600s"  # 10 minutes
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  alert_strategy {
    auto_close = "3600s"  # 1 hour
  }

  combiner = "OR"
  enabled  = true

  dynamic "notification_channels" {
    for_each = var.notification_channels
    content {
      notification_channels = [notification_channels.value]
    }
  }
}

# Custom metric for analysis completion rate
resource "google_logging_metric" "analysis_completion_rate" {
  count = var.enable_custom_metrics ? 1 : 0
  
  name    = "${var.function_name}_analysis_completion_rate"
  project = var.project_id
  
  filter = <<-EOT
    resource.type="cloud_function"
    resource.labels.function_name="${var.function_name}"
    jsonPayload.message="Analysis completed successfully"
  EOT
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "INT64"
    display_name = "User Activity Analysis Completion Rate"
    description = "Rate of successful analysis completions"
  }
  
  value_extractor = "EXTRACT(jsonPayload.users_processed)"
  
  label_extractors = {
    environment = "EXTRACT(jsonPayload.environment)"
    batch_size  = "EXTRACT(jsonPayload.batch_size)"
  }
}

# Custom metric for analysis errors
resource "google_logging_metric" "analysis_errors" {
  count = var.enable_custom_metrics ? 1 : 0
  
  name    = "${var.function_name}_analysis_errors"
  project = var.project_id
  
  filter = <<-EOT
    resource.type="cloud_function"
    resource.labels.function_name="${var.function_name}"
    (severity>=ERROR OR jsonPayload.level="ERROR")
  EOT
  
  metric_descriptor {
    metric_kind = "COUNTER"
    value_type  = "INT64"
    display_name = "User Activity Analysis Errors"
    description = "Count of analysis errors"
  }
  
  label_extractors = {
    error_type  = "EXTRACT(jsonPayload.error_type)"
    environment = "EXTRACT(jsonPayload.environment)"
  }
}

# Dashboard for system health monitoring
resource "google_monitoring_dashboard" "user_activity_analysis" {
  count = var.enable_monitoring_dashboard ? 1 : 0
  
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "User Activity Analysis System Health"
    mosaicLayout = {
      tiles = [
        {
          width = 6
          height = 4
          widget = {
            title = "Function Execution Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" resource.label.function_name=\"${var.function_name}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_count\""
                    aggregation = {
                      alignmentPeriod = "300s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Executions/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width = 6
          height = 4
          xPos = 6
          widget = {
            title = "Function Error Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" resource.label.function_name=\"${var.function_name}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" metric.label.status!=\"ok\""
                    aggregation = {
                      alignmentPeriod = "300s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Errors/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width = 6
          height = 4
          yPos = 4
          widget = {
            title = "Function Execution Time (95th percentile)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" resource.label.function_name=\"${var.function_name}\" metric.type=\"cloudfunctions.googleapis.com/function/execution_times\""
                    aggregation = {
                      alignmentPeriod = "300s"
                      perSeriesAligner = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Duration (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width = 6
          height = 4
          xPos = 6
          yPos = 4
          widget = {
            title = "Scheduler Job Success Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_scheduler_job\" resource.label.job_id=\"${var.scheduler_job_name}\" metric.type=\"cloudscheduler.googleapis.com/job/num_attempts\" metric.label.response_code=\"200\""
                    aggregation = {
                      alignmentPeriod = "3600s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Success Rate"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}

# IAM binding to allow Cloud Scheduler to invoke the function
resource "google_cloudfunctions2_function_iam_binding" "user_activity_analysis_invoker" {
  project        = google_cloudfunctions2_function.function.project
  location       = google_cloudfunctions2_function.function.location
  cloud_function = google_cloudfunctions2_function.function.name
  role           = "roles/cloudfunctions.invoker"
  members = [
    "serviceAccount:${var.service_account_email}"
  ]
}

# Data sources for existing secrets
data "google_secret_manager_secret" "cloud_sql_instance_connection_name" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
}

data "google_secret_manager_secret" "cloud_sql_database_name" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_DATABASE_NAME"
}

data "google_secret_manager_secret" "cloud_sql_user" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_USER"
}

data "google_secret_manager_secret" "cloud_sql_password" {
  project   = var.project_id
  secret_id = "CLOUD_SQL_PASSWORD"
}

data "google_secret_manager_secret" "openrouter_api_key" {
  project   = var.project_id
  secret_id = "OPENROUTER_API_KEY"
}

# Grant the function's service account access to the secrets
resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_instance_connection_name" {
  project   = data.google_secret_manager_secret.cloud_sql_instance_connection_name.project
  secret_id = data.google_secret_manager_secret.cloud_sql_instance_connection_name.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_database_name" {
  project   = data.google_secret_manager_secret.cloud_sql_database_name.project
  secret_id = data.google_secret_manager_secret.cloud_sql_database_name.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_user" {
  project   = data.google_secret_manager_secret.cloud_sql_user.project
  secret_id = data.google_secret_manager_secret.cloud_sql_user.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_cloud_sql_password" {
  project   = data.google_secret_manager_secret.cloud_sql_password.project
  secret_id = data.google_secret_manager_secret.cloud_sql_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "secret_access_openrouter_key" {
  project   = data.google_secret_manager_secret.openrouter_api_key.project
  secret_id = data.google_secret_manager_secret.openrouter_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}