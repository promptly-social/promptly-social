# Unified Post Scheduler Cloud Function

This Cloud Function processes all scheduled posts every 5 minutes, replacing the individual Cloud Scheduler jobs approach.

## Overview

The unified post scheduler:
- Runs every 5 minutes via Cloud Scheduler
- Queries for posts scheduled in the last 5 minutes
- Publishes posts to LinkedIn on behalf of users
- Updates post status after successful/failed publishing
- Provides comprehensive logging and error handling

## Environment Variables

Required environment variables:

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `LINKEDIN_CLIENT_ID`: LinkedIn OAuth client ID
- `LINKEDIN_CLIENT_SECRET`: LinkedIn OAuth client secret
- `LINKEDIN_TOKEN_REFRESH_THRESHOLD`: Minutes before expiry to refresh token (default: 60)
- `MAX_RETRY_ATTEMPTS`: Maximum retry attempts for operations (default: 3)

## Function Behavior

1. **Query Phase**: Finds posts with status='scheduled' and scheduled_at between 5 minutes ago and now
2. **Processing Phase**: For each post:
   - Retrieves user's LinkedIn connection
   - Refreshes access token if needed
   - Gets post media attachments
   - Publishes to LinkedIn
   - Updates post status
3. **Completion**: Returns summary of processed posts

## Error Handling

- Individual post failures don't stop processing of other posts
- Failed posts are marked with error status for retry
- Comprehensive logging for debugging
- Exponential backoff retry logic for transient failures

## Deployment

This function is deployed via Terraform configuration in the `terraform/modules/unified_post_scheduler_function/` module.

## Testing

Local testing can be done by setting environment variables and calling the function with a test request.

## Monitoring

The function logs:
- Execution start/completion times
- Number of posts found and processed
- Success/failure counts
- Individual post processing results
- Detailed error information for failures