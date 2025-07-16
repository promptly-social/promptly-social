# Design Document

## Overview

The share-post cloud function is a Google Cloud Function that automatically shares posts to LinkedIn at scheduled times. It integrates with the existing infrastructure by following established patterns from analyze-substack and generate-suggestions functions. The function will be triggered by Cloud Scheduler jobs that are managed through a new post scheduling service, similar to the existing daily suggestion schedule service.

## Architecture

### High-Level Flow

1. User schedules a post through the backend API
2. Backend creates/updates Cloud Scheduler job for the scheduled time
3. Cloud Scheduler triggers the share-post function at the specified time
4. Function retrieves post data and user's LinkedIn connection
5. Function uses existing LinkedIn service logic to share the post
6. Function updates post status and records sharing results

### Components Integration

- **Cloud Function**: New share-post function following existing patterns
- **Cloud Scheduler**: Manages scheduled post sharing jobs
- **Backend Service**: New PostScheduleService for managing scheduler jobs
- **Database**: Extended posts table with scheduling fields
- **LinkedIn Service**: Reused existing service for actual sharing

## Components and Interfaces

### 1. Share-Post Cloud Function

**Location**: `terraform/src/gcp-functions/share-post/`

**Entry Point**: `share_post(request)`

**Request Format**:

```json
{
  "user_id": "uuid",
  "post_id": "uuid"
}
```

**Response Format**:

```json
{
  "success": true,
  "message": "Post shared successfully",
  "linkedin_post_id": "linkedin_post_id",
  "shared_at": "2024-01-01T12:00:00Z"
}
```

**Key Functions**:

- `get_supabase_client()`: Initialize database client
- `get_post_data(user_id, post_id)`: Retrieve post from database
- `get_linkedin_connection(user_id)`: Get user's LinkedIn credentials
- `refresh_token_if_needed(connection)`: Handle token refresh
- `share_to_linkedin(post_data, connection)`: Execute the sharing
- `update_post_status(post_id, result)`: Update database with results

### 2. Post Schedule Service

**Location**: `backend/app/services/post_schedule.py`

**Pattern**: Similar to `DailySuggestionScheduleService`

**Key Methods**:

- `schedule_post(user_id, post_id, scheduled_at, timezone)`: Create scheduler job
- `unschedule_post(user_id, post_id)`: Remove scheduler job
- `reschedule_post(user_id, post_id, new_scheduled_at)`: Update scheduler job
- `_create_scheduler_job(post_id, scheduled_at, timezone)`: Internal job creation
- `_delete_scheduler_job(job_name)`: Internal job deletion

### 3. Database Schema Extensions

**Posts Table Additions**:

```sql
ALTER TABLE posts ADD COLUMN scheduled_at TIMESTAMPTZ;
ALTER TABLE posts ADD COLUMN scheduler_job_name VARCHAR(255);
ALTER TABLE posts ADD COLUMN linkedin_post_id VARCHAR(255);
ALTER TABLE posts ADD COLUMN shared_at TIMESTAMPTZ;
ALTER TABLE posts ADD COLUMN sharing_error TEXT;
```

**Indexes**:

```sql
CREATE INDEX idx_posts_scheduled_at ON posts(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX idx_posts_scheduler_job_name ON posts(scheduler_job_name) WHERE scheduler_job_name IS NOT NULL;
```

### 4. Terraform Infrastructure

**New Module**: `terraform/modules/share_post_function/`

**Resources**:

- Cloud Function with Python 3.13 runtime
- Service Account with minimal required permissions
- IAM bindings for secret access and Cloud Scheduler invocation
- Storage bucket object for function source code
- Secret Manager integration for environment variables

**Required Secrets**:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `GCP_SHARE_POST_FUNCTION_URL` (stored after deployment)

**Environment Variables**:

- `LINKEDIN_TOKEN_REFRESH_THRESHOLD`: Time before expiry to refresh tokens
- `MAX_RETRY_ATTEMPTS`: Number of retry attempts for failed operations

### 5. API Endpoints Extensions

**New Endpoints in Posts Router**:

- `POST /posts/{post_id}/schedule`: Schedule a post
- `DELETE /posts/{post_id}/schedule`: Unschedule a post
- `PUT /posts/{post_id}/schedule`: Reschedule a post

**Request/Response Schemas**:

```python
class PostScheduleRequest(BaseModel):
    scheduled_at: datetime
    timezone: str = "UTC"

class PostScheduleResponse(BaseModel):
    success: bool
    scheduled_at: datetime
    scheduler_job_name: str
```

## Data Models

### Extended Post Model

```python
class Post(Base):
    # ... existing fields ...
    scheduled_at: Optional[datetime] = Column(DateTime(timezone=True))
    scheduler_job_name: Optional[str] = Column(String(255))
    linkedin_post_id: Optional[str] = Column(String(255))
    shared_at: Optional[datetime] = Column(DateTime(timezone=True))
    sharing_error: Optional[str] = Column(Text)
```

### Cloud Scheduler Job Naming Convention

**Pattern**: `share-post-{post_id}`

**Example**: `share-post-123e4567-e89b-12d3-a456-426614174000`

This ensures unique job names and easy identification of which post each job is for.

## Error Handling

### Token Refresh Strategy

1. Check token expiry before sharing
2. If token expires within threshold, attempt refresh
3. If refresh succeeds, update stored connection data
4. If refresh fails, mark connection as invalid and log error
5. Retry original sharing operation with new token

### Retry Logic

1. Database connection failures: Exponential backoff, max 3 retries
2. LinkedIn API failures: Immediate retry once, then fail
3. Token refresh failures: No retry, mark as authentication error
4. Scheduler job failures: Log error but don't fail the sharing operation

### Error Logging

- All errors logged with structured data including user_id, post_id, error_type
- Critical errors (authentication failures) trigger alerts
- Transient errors (network timeouts) logged as warnings

### Graceful Degradation

- If LinkedIn API is unavailable, mark post for retry later
- If database is unavailable, log to Cloud Logging for manual intervention
- If token refresh fails, notify user through existing notification system

## Testing Strategy

### Unit Tests

- **Function Logic**: Test core sharing logic with mocked dependencies
- **Token Refresh**: Test token refresh scenarios and edge cases
- **Error Handling**: Test all error conditions and retry logic
- **Data Validation**: Test input validation and sanitization

### Integration Tests

- **Database Operations**: Test post retrieval and status updates
- **LinkedIn Integration**: Test actual sharing with test LinkedIn account
- **Scheduler Integration**: Test job creation and deletion
- **End-to-End**: Test complete flow from scheduling to sharing

### Local Testing

- **Mock Environment**: Use local test environment with mocked Cloud Scheduler
- **Test Data**: Create test posts and LinkedIn connections
- **Error Simulation**: Simulate various failure scenarios
- **Performance Testing**: Test function performance under load

### Deployment Testing

- **Staging Environment**: Deploy to staging and test with real LinkedIn API
- **Production Validation**: Smoke tests after production deployment
- **Monitoring**: Set up alerts for function failures and performance issues

## Security Considerations

### Authentication

- Function uses service account with minimal required permissions
- LinkedIn tokens stored encrypted in database
- All API calls use HTTPS and proper authentication headers

### Authorization

- Function validates user ownership of posts before sharing
- Cloud Scheduler jobs include user context for validation
- No sensitive data exposed in logs or error messages

### Data Protection

- LinkedIn tokens refreshed and stored securely
- Post content sanitized before sharing
- Audit trail maintained for all sharing operations

## Performance Considerations

### Function Optimization

- Cold start minimization through proper dependency management
- Connection pooling for database operations
- Efficient token refresh logic to minimize API calls

### Scalability

- Function configured for concurrent execution
- Database queries optimized with proper indexes
- Cloud Scheduler jobs distributed across time to avoid spikes

### Monitoring

- Function execution time and memory usage tracked
- LinkedIn API rate limiting monitored and respected
- Database connection pool health monitored

## Deployment Strategy

### Infrastructure as Code

- All resources defined in Terraform modules
- Environment-specific configurations in separate files
- Automated deployment through GitHub Actions

### Blue-Green Deployment

- New function versions deployed alongside existing ones
- Traffic gradually shifted to new versions
- Rollback capability maintained for quick recovery

### Environment Promotion

- Changes tested in staging environment first
- Automated promotion to production after validation
- Database migrations applied before function deployment
