#!/bin/bash

# User Activity Analysis Scheduler Management Script
# This script provides operational commands for managing the scheduler job

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
JOB_NAME="${JOB_NAME:-user-activity-analysis-trigger}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    if [ -z "$PROJECT_ID" ]; then
        log_error "PROJECT_ID environment variable is required"
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is required but not installed"
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
        log_error "Please authenticate with gcloud first: gcloud auth login"
        exit 1
    fi
}

show_status() {
    log_info "Checking scheduler job status..."
    gcloud scheduler jobs describe "$JOB_NAME" \
        --location="$REGION" \
        --project="$PROJECT_ID" \
        --format="table(name,schedule,timeZone,state,lastAttemptTime,nextRunTime)"
}

pause_job() {
    log_info "Pausing scheduler job: $JOB_NAME"
    gcloud scheduler jobs pause "$JOB_NAME" \
        --location="$REGION" \
        --project="$PROJECT_ID"
    log_info "Job paused successfully"
}

resume_job() {
    log_info "Resuming scheduler job: $JOB_NAME"
    gcloud scheduler jobs resume "$JOB_NAME" \
        --location="$REGION" \
        --project="$PROJECT_ID"
    log_info "Job resumed successfully"
}

run_now() {
    log_info "Triggering immediate execution of scheduler job: $JOB_NAME"
    gcloud scheduler jobs run "$JOB_NAME" \
        --location="$REGION" \
        --project="$PROJECT_ID"
    log_info "Job triggered successfully"
}

show_logs() {
    local hours=${1:-1}
    log_info "Showing logs for the last $hours hour(s)..."
    gcloud logging read "
        resource.type=\"cloud_scheduler_job\"
        resource.labels.job_id=\"$JOB_NAME\"
        resource.labels.location=\"$REGION\"
        timestamp >= \"$(date -u -d "$hours hours ago" '+%Y-%m-%dT%H:%M:%SZ')\"
    " \
        --project="$PROJECT_ID" \
        --format="table(timestamp,severity,jsonPayload.status,jsonPayload.targetType)" \
        --limit=50
}

show_function_logs() {
    local hours=${1:-1}
    log_info "Showing function logs for the last $hours hour(s)..."
    gcloud logging read "
        resource.type=\"cloud_function\"
        resource.labels.function_name=\"user-activity-analysis\"
        timestamp >= \"$(date -u -d "$hours hours ago" '+%Y-%m-%dT%H:%M:%SZ')\"
    " \
        --project="$PROJECT_ID" \
        --format="table(timestamp,severity,textPayload)" \
        --limit=100
}

update_schedule() {
    local new_schedule="$1"
    if [ -z "$new_schedule" ]; then
        log_error "New schedule is required. Example: '0 */2 * * *' for every 2 hours"
        exit 1
    fi
    
    log_info "Updating scheduler job schedule to: $new_schedule"
    gcloud scheduler jobs update http "$JOB_NAME" \
        --location="$REGION" \
        --project="$PROJECT_ID" \
        --schedule="$new_schedule"
    log_info "Schedule updated successfully"
}

show_help() {
    cat << EOF
User Activity Analysis Scheduler Management Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    status              Show current job status and next run time
    pause               Pause the scheduler job
    resume              Resume the scheduler job
    run                 Trigger immediate execution
    logs [HOURS]        Show scheduler logs (default: 1 hour)
    function-logs [HOURS] Show function execution logs (default: 1 hour)
    update-schedule CRON Update the job schedule (e.g., '0 */2 * * *')
    help                Show this help message

Environment Variables:
    PROJECT_ID          GCP project ID (required)
    REGION              GCP region (default: us-central1)
    JOB_NAME            Scheduler job name (default: user-activity-analysis-trigger)

Examples:
    $0 status
    $0 pause
    $0 resume
    $0 run
    $0 logs 2
    $0 function-logs 6
    $0 update-schedule "0 */2 * * *"

EOF
}

# Main script logic
main() {
    check_prerequisites
    
    case "${1:-help}" in
        status)
            show_status
            ;;
        pause)
            pause_job
            ;;
        resume)
            resume_job
            ;;
        run)
            run_now
            ;;
        logs)
            show_logs "${2:-1}"
            ;;
        function-logs)
            show_function_logs "${2:-1}"
            ;;
        update-schedule)
            update_schedule "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"