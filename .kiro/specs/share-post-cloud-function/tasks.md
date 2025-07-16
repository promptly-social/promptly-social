# Implementation Plan

- [x] 1. Create database schema migration for post scheduling

  - Create Supabase migration script to add scheduling fields to posts table
  - Add scheduled_at, scheduler_job_name, linkedin_post_id, shared_at, sharing_error columns
  - Create indexes for performance optimization on scheduled_at and scheduler_job_name
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2. Update Post model and schemas with scheduling fields

  - Modify Post model in backend/app/models/posts.py to include new scheduling fields
  - Update PostResponse schema to include scheduling information
  - Create new PostScheduleRequest and PostScheduleResponse schemas
  - _Requirements: 8.1, 8.3, 8.6_

- [x] 3. Create PostScheduleService for managing Cloud Scheduler jobs

  - Create backend/app/services/post_schedule.py following DailySuggestionScheduleService pattern
  - Implement schedule_post, unschedule_post, and reschedule_post methods
  - Add Cloud Scheduler client integration with proper error handling
  - Implement job naming convention and CRUD operations for scheduler jobs
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.1, 8.2, 8.3_

- [x] 4. Extend Posts router with scheduling endpoints

  - Add POST /posts/{post_id}/schedule endpoint for scheduling posts
  - Add DELETE /posts/{post_id}/schedule endpoint for unscheduling posts
  - Add PUT /posts/{post_id}/schedule endpoint for rescheduling posts
  - Implement proper authentication and authorization checks
  - _Requirements: 8.1, 8.6_

- [x] 5. Create share-post cloud function structure and main logic

  - Create terraform/src/gcp-functions/share-post/ directory structure
  - Implement main.py with share_post function entry point
  - Add request validation and CORS handling following existing patterns
  - Implement get_supabase_client function for database connectivity
  - _Requirements: 1.1, 1.2, 8.1, 8.2_

- [x] 6. Implement post retrieval and validation logic

  - Create get_post_data function to retrieve post from database
  - Add validation to ensure post belongs to the specified user
  - Implement checks for post status and scheduling information
  - Add error handling for missing or invalid posts
  - _Requirements: 1.1, 1.2, 5.1, 8.5_

- [x] 7. Implement LinkedIn connection and token management

  - Create get_linkedin_connection function to retrieve user's LinkedIn credentials
  - Implement refresh_token_if_needed function for automatic token refresh
  - Add token expiry validation and refresh logic
  - Update stored connection data with new tokens after refresh
  - _Requirements: 1.3, 3.1, 3.2, 3.3, 8.5_

- [x] 8. Implement LinkedIn post sharing logic

  - Create share_to_linkedin function using existing LinkedInService patterns
  - Handle post content, article URLs, and media attachments
  - Implement proper error handling for LinkedIn API failures
  - Add support for visibility settings and post formatting
  - _Requirements: 1.4, 1.5, 5.2, 5.3, 5.4_

- [x] 9. Implement post status updates and result tracking

  - Create update_post_status function to record sharing results
  - Update post status to "posted" and record posted timestamp
  - Store LinkedIn post ID for future reference
  - Handle and store error information for failed sharing attempts
  - _Requirements: 1.6, 1.7, 5.5, 5.6_

- [x] 10. Add comprehensive error handling and retry logic

  - Implement exponential backoff for database connection failures
  - Add retry logic for transient LinkedIn API errors
  - Create structured error logging with user_id and post_id context
  - Handle authentication errors and connection failures gracefully
  - _Requirements: 3.4, 3.5, 8.4_

- [x] 11. Create requirements.txt and function dependencies

  - Create requirements.txt with necessary Python packages
  - Include supabase, httpx, google-cloud-secret-manager, and other dependencies
  - Follow existing patterns from analyze-substack and generate-suggestions functions
  - _Requirements: 8.1, 8.2_

- [x] 12. Create Terraform module for share-post function

  - Create terraform/modules/share_post_function/ directory
  - Implement main.tf following existing function module patterns
  - Configure Cloud Function with Python 3.13 runtime and proper settings
  - Set up service account with minimal required permissions
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 13. Configure Terraform module variables and outputs

  - Create variables.tf with all necessary input variables
  - Create outputs.tf to expose function URL and other important values
  - Follow existing patterns from analyze_substack_function and generate_suggestions_function modules
  - _Requirements: 2.1, 2.2_

- [x] 14. Set up IAM permissions and secret access

  - Configure service account IAM bindings for secret manager access
  - Grant Cloud Scheduler permission to invoke the function
  - Set up proper IAM roles for Cloud Build and deployment
  - Configure secret environment variables for Supabase and other services
  - _Requirements: 2.2, 2.5, 2.6_

- [x] 15. Create staging and production Terraform environments

  - Create terraform/environments/share_post/staging/ configuration
  - Create terraform/environments/share_post/production/ configuration
  - Set up backend configuration and environment-specific variables
  - Follow existing patterns from other function environments
  - _Requirements: 2.4, 4.1, 4.2_

- [x] 16. Create GitHub Actions deployment workflow

  - Create .github/workflows/deploy-share-post.yml following existing patterns
  - Configure automated deployment to staging on main branch pushes
  - Add manual deployment option for production environment
  - Set up proper authentication and deployment steps
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 17. Add Cloud Scheduler permissions to existing infrastructure

  - Update existing Terraform modules to include cloudscheduler.googleapis.com API
  - Add Cloud Scheduler admin permissions to necessary service accounts
  - Update IAM bindings for scheduler job management
  - _Requirements: 2.2, 2.5_

- [x] 18. Create unit tests for the cloud function

  - Create test files for main function logic with mocked dependencies
  - Test post retrieval, LinkedIn connection, and sharing logic
  - Add tests for error handling and retry scenarios
  - Test token refresh functionality and edge cases
  - _Requirements: 8.1, 8.4_

- [x] 19. Create integration tests for PostScheduleService

  - Test Cloud Scheduler job creation, update, and deletion
  - Test integration with posts database operations
  - Add tests for error handling and edge cases
  - Test job naming conventions and uniqueness
  - _Requirements: 8.1, 8.3, 8.5_

- [x] 20. Update existing posts service to integrate with scheduling

  - Modify PostsService to handle scheduling operations
  - Update create_post and update_post methods to work with scheduling
  - Add validation for scheduling constraints and business rules
  - Integrate with PostScheduleService for scheduler job management
  - _Requirements: 8.1, 8.3, 8.5_

- [x] 21. Test end-to-end functionality in staging environment

  - Deploy function to staging and test with real LinkedIn API
  - Create test posts and schedule them for sharing
  - Verify Cloud Scheduler job creation and execution
  - Test error scenarios and recovery mechanisms
  - _Requirements: 4.1, 4.4_

- [x] 22. Add monitoring and alerting configuration

  - Set up Cloud Monitoring for function execution metrics
  - Configure alerts for function failures and performance issues
  - Add structured logging for debugging and monitoring
  - Set up dashboard for tracking sharing success rates
  - _Requirements: 2.6_

- [x] 23. Create documentation and deployment guide

  - Document the new scheduling API endpoints
  - Create deployment and configuration guide
  - Document troubleshooting steps for common issues
  - Update existing API documentation with new functionality
  - _Requirements: 8.1_

- [x] 24. Deploy to production and validate functionality
  - Deploy infrastructure and function to production environment
  - Run smoke tests to verify basic functionality
  - Monitor initial deployments for any issues
  - Validate integration with existing production systems
  - _Requirements: 4.2, 4.4, 4.5_
