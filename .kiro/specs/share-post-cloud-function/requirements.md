# Requirements Document

## Introduction

This feature implements a new Google Cloud Function called "share-post" that enables automated sharing of posts to LinkedIn. The function will retrieve user posts from the database, fetch the latest LinkedIn access tokens, and use the existing LinkedIn service logic to publish posts with their associated content including article URLs and media attachments.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want a cloud function that can share posts to LinkedIn automatically, so that users' scheduled posts are published without manual intervention.

#### Acceptance Criteria

1. WHEN the share-post function is triggered with a user_id and post_id THEN the system SHALL retrieve the post from the database
2. WHEN a valid post is found THEN the system SHALL fetch the user's LinkedIn connection data including access token
3. WHEN the LinkedIn connection is valid THEN the system SHALL use the existing LinkedIn service to share the post
4. IF the post contains an article URL THEN the system SHALL include it in the LinkedIn share
5. IF the post contains media attachments THEN the system SHALL upload and include them in the LinkedIn share
6. WHEN the post is successfully shared THEN the system SHALL update the post status to "posted" and record the posted timestamp
7. IF any step fails THEN the system SHALL log the error and return appropriate error response

### Requirement 2

**User Story:** As a developer, I want proper Terraform infrastructure provisioning for the share-post function, so that it can be deployed consistently across environments.

#### Acceptance Criteria

1. WHEN deploying the function THEN the system SHALL create a new Terraform module for the share-post function
2. WHEN provisioning resources THEN the system SHALL configure proper IAM roles and permissions for database access
3. WHEN setting up the function THEN the system SHALL configure environment variables for database connection and API keys
4. WHEN deploying THEN the system SHALL create separate staging and production environments
5. WHEN configuring security THEN the system SHALL ensure the function has minimal required permissions
6. WHEN setting up monitoring THEN the system SHALL configure appropriate logging and error tracking

### Requirement 3

**User Story:** As a system, I want proper error handling and token refresh capabilities, so that the share-post function remains reliable even when access tokens expire.

#### Acceptance Criteria

1. WHEN the LinkedIn access token is expired THEN the system SHALL attempt to refresh it using the refresh token
2. WHEN token refresh succeeds THEN the system SHALL update the stored connection data with new tokens
3. WHEN token refresh fails THEN the system SHALL log the error and mark the connection as invalid
4. WHEN database operations fail THEN the system SHALL retry with exponential backoff up to 3 times
5. WHEN LinkedIn API calls fail THEN the system SHALL log detailed error information for debugging
6. WHEN any unrecoverable error occurs THEN the system SHALL return appropriate HTTP status codes

### Requirement 4

**User Story:** As a DevOps engineer, I want automated deployment pipelines for the share-post function, so that updates can be deployed safely and consistently.

#### Acceptance Criteria

1. WHEN code changes are pushed to main branch THEN the system SHALL trigger automated deployment to staging
2. WHEN manual deployment is requested THEN the system SHALL allow selection of staging or production environment
3. WHEN deploying THEN the system SHALL use the same authentication and deployment patterns as existing functions
4. WHEN deployment completes THEN the system SHALL verify the function is accessible and responding
5. WHEN deployment fails THEN the system SHALL provide clear error messages and rollback if necessary

### Requirement 5

**User Story:** As a user, I want my posts to be shared exactly as configured, so that my LinkedIn presence maintains consistency with my content strategy.

#### Acceptance Criteria

1. WHEN sharing a post THEN the system SHALL preserve the exact text content from the database
2. WHEN a post has an article URL THEN the system SHALL include it as a link preview in the LinkedIn post
3. WHEN a post has media attachments THEN the system SHALL upload them to LinkedIn and include in the post
4. WHEN sharing THEN the system SHALL use the visibility setting configured for the user (PUBLIC or CONNECTIONS)
5. WHEN the post is shared successfully THEN the system SHALL record the LinkedIn post ID for future reference
6. WHEN sharing fails THEN the system SHALL preserve the original post data and allow for retry

### Requirement 6

**User Story:** As a user, I want my scheduled posts to be automatically shared at the specified time, so that my content is published according to my posting schedule.

#### Acceptance Criteria

1. WHEN a post is scheduled THEN the system SHALL create a Cloud Scheduler job that triggers the share-post function at the specified time
2. WHEN a post is unscheduled THEN the system SHALL remove the corresponding Cloud Scheduler job
3. WHEN a post schedule is updated THEN the system SHALL update the existing Cloud Scheduler job with the new timing
4. WHEN creating scheduler jobs THEN the system SHALL store cron_expression and timezone similar to dailySuggestionSchedule pattern
5. WHEN the scheduled time arrives THEN the Cloud Scheduler SHALL trigger the share-post function with the appropriate user_id and post_id
6. WHEN scheduler jobs are created THEN the system SHALL use unique job names to avoid conflicts

### Requirement 7

**User Story:** As a developer, I want proper database schema changes with migration scripts, so that the system can track scheduling information and maintain data integrity.

#### Acceptance Criteria

1. WHEN database schema changes are needed THEN the system SHALL create appropriate Supabase migration scripts
2. WHEN adding scheduling fields THEN the system SHALL follow the existing pattern used by dailySuggestionSchedule
3. WHEN creating migrations THEN the system SHALL include proper indexes for performance
4. WHEN updating schema THEN the system SHALL ensure backward compatibility during deployment
5. WHEN adding new fields THEN the system SHALL provide appropriate default values

### Requirement 8

**User Story:** As a developer, I want to follow established coding and implementation patterns, so that the new functionality integrates seamlessly with the existing codebase.

#### Acceptance Criteria

1. WHEN implementing the function THEN the system SHALL follow the existing patterns used in analyze-substack and generate-suggestions functions
2. WHEN writing code THEN the system SHALL adhere to the established coding standards and conventions
3. WHEN creating services THEN the system SHALL follow the existing service layer patterns
4. WHEN handling errors THEN the system SHALL use consistent error handling approaches
5. WHEN implementing database operations THEN the system SHALL follow existing ORM and query patterns
6. WHEN creating API endpoints THEN the system SHALL follow existing authentication and authorization patterns