# Share Post Cloud Function

This Google Cloud Function automatically shares scheduled posts to LinkedIn at their designated times. It's triggered by Google Cloud Scheduler jobs that are managed through the backend API.

## Overview

The share-post function is part of the post scheduling system that allows users to schedule their posts for automatic sharing to LinkedIn. When a post is scheduled, a Cloud Scheduler job is created that triggers this function at the specified time.

## Function Flow

1. **Triggered by Cloud Scheduler**: The function is called with `user_id` and `post_id` parameters
2. **Post Validation**: Retrieves and validates the post from the database
3. **LinkedIn Connection**: Gets the user's LinkedIn connection and credentials
4. **Token Refresh**: Automatically refreshes LinkedIn access tokens if needed
5. **Media Handling**: Retrieves any media attachments for the post
6. **LinkedIn Sharing**: Shares the post to LinkedIn using their API
7. **Status Update**: Updates the post status to "posted" and records sharing details

## API Specification

### Request Format
```json
{
  "user_id": "uuid",
  "post_id": "uuid"
}
```

### Response Format (Success)
```json
{
  "success": true,
  "message": "Post shared successfully",
  "linkedin_post_id": "linkedin_post_id",
  "shared_at": "2024-01-01T12:00:00Z"
}
```

### Response Format (Error)
```json
{
  "success": false,
  "error": "Error description"
}
```

## Environment Variables

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `LINKEDIN_CLIENT_ID`: LinkedIn OAuth client ID
- `LINKEDIN_CLIENT_SECRET`: LinkedIn OAuth client secret
- `LINKEDIN_TOKEN_REFRESH_THRESHOLD`: Minutes before expiry to refresh tokens (default: 60)
- `MAX_RETRY_ATTEMPTS`: Maximum retry attempts for failed operations (default: 3)

## Error Handling

The function includes comprehensive error handling:

- **Database Errors**: Retry with exponential backoff (up to 3 attempts)
- **LinkedIn API Errors**: Single retry for transient errors
- **Token Refresh**: Automatic refresh when tokens are near expiry
- **Authentication Failures**: Proper error logging and status updates

## Testing

### Unit Tests
Run the unit tests with:
```bash
python -m pytest test_main.py -v
```

### Local Testing
For local testing, you can use the test script:
```bash
python test_main_local.py
```

## Deployment

The function is deployed using Terraform and GitHub Actions:

1. **Staging**: Automatically deployed when changes are pushed to main branch
2. **Production**: Manually deployed through GitHub Actions workflow

### Manual Deployment
```bash
# Navigate to the appropriate environment
cd terraform/environments/share_post/staging

# Initialize and apply
terraform init
terraform plan
terraform apply
```

## Monitoring

The function includes structured logging for monitoring:

- **Success Events**: Logged with post_id and sharing details
- **Error Events**: Logged with error context and retry information
- **Performance Metrics**: Function execution time and memory usage

## Security

- **IAM**: Function runs with minimal required permissions
- **Secrets**: All sensitive data stored in Google Secret Manager
- **Network**: Function configured with `ALLOW_INTERNAL_ONLY` ingress
- **Authentication**: Cloud Scheduler uses OIDC tokens for authentication

## Troubleshooting

### Common Issues

1. **Token Refresh Failures**
   - Check LinkedIn client credentials in Secret Manager
   - Verify refresh token is still valid
   - Check token expiry dates

2. **Database Connection Issues**
   - Verify Supabase credentials
   - Check network connectivity
   - Review database permissions

3. **LinkedIn API Errors**
   - Check LinkedIn API status
   - Verify post content meets LinkedIn requirements
   - Review rate limiting

### Logs
Function logs are available in Google Cloud Logging:
```bash
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=share-post-staging"
```

## Related Components

- **PostScheduleService**: Backend service for managing Cloud Scheduler jobs
- **Posts API**: REST endpoints for scheduling and managing posts
- **LinkedIn Service**: Shared LinkedIn integration logic
- **Cloud Scheduler**: Google service for triggering the function at scheduled times