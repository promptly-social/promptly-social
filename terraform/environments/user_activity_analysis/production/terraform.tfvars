# Project configuration
project_id  = "promptly-social"
region      = "us-central1"
app_name    = "promptly"
environment = "production"

# Scheduler configuration - once daily at midnight PDT
schedule         = "0 7 * * *"  # 7 AM UTC = midnight PDT (UTC-7)
timezone         = "America/Los_Angeles"
scheduler_paused = false

# Analysis configuration for staging
openrouter_model_primary     = "google/gemini-2.5-flash"
openrouter_models_fallback   = ["meta-llama/llama-4-maverick"]
openrouter_model_temperature = "0.0"

# Lower thresholds for staging environment
post_threshold            = 5
message_threshold         = 8
max_retry_attempts        = 1
analysis_timeout_minutes  = 15
batch_size               = 5

# Monitoring configuration
enable_monitoring_alerts    = false  # Temporarily disabled
enable_custom_metrics       = false  # Temporarily disabled
enable_monitoring_dashboard = false  # Temporarily disabled
enable_scheduler_monitoring = false  # Temporarily disabled

# Alert thresholds (more lenient for staging)
error_rate_threshold        = 0.2
execution_time_threshold_ms = 720000  # 12 minutes
scheduler_failure_threshold = 3
