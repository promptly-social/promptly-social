# Requirements Document

## Introduction

This feature adds a "Post Now" button to the PostCardActions component that allows users to immediately publish their posts to LinkedIn. The feature includes proper loading states, error handling, and visual error indicators to provide a seamless user experience when publishing posts directly from the interface.

## Requirements

### Requirement 1

**User Story:** As a user, I want to publish my post to LinkedIn immediately, so that I can share content without having to schedule it first.

#### Acceptance Criteria

1. WHEN a user views a post card THEN the system SHALL display a "Post Now" button for posts that are not already posted
2. WHEN a user clicks the "Post Now" button THEN the system SHALL show a loading state with appropriate visual feedback
3. WHEN the post is successfully published THEN the system SHALL update the post status to "posted" and show a success message
4. WHEN the post publishing completes THEN the system SHALL refresh the post data to reflect the new status

### Requirement 2

**User Story:** As a user, I want to see clear feedback when posting fails, so that I understand what happened and can take appropriate action.

#### Acceptance Criteria

1. WHEN post publishing fails THEN the system SHALL maintain the original post status (e.g., "scheduled", "draft")
2. WHEN post publishing fails THEN the system SHALL store the error message in the sharing_error column
3. WHEN post publishing fails THEN the system SHALL display an error toast notification
4. WHEN the posting operation fails THEN the system SHALL stop the loading state and return to the normal button state

### Requirement 3

**User Story:** As a user, I want to see visual indicators when a post has sharing errors, so that I'm aware of failed posting attempts and can retry.

#### Acceptance Criteria

1. WHEN a post has a sharing_error value THEN the system SHALL display an error indicator on the post card
2. WHEN a user sees the error indicator THEN the system SHALL show a user-friendly message like "An error occurred when Promptly tried to post on your behalf. Please try to reschedule it or post it now"
3. WHEN a post is successfully published after a previous error THEN the system SHALL clear the sharing_error field
4. WHEN displaying the error message THEN the system SHALL NOT expose technical error details to the user

### Requirement 4

**User Story:** As a user, I want the "Post Now" button to be appropriately positioned and styled, so that it fits naturally with the existing interface.

#### Acceptance Criteria

1. WHEN viewing post cards THEN the "Post Now" button SHALL be positioned logically within the PostCardActions component
2. WHEN the post status is "posted" THEN the system SHALL NOT display the "Post Now" button
3. WHEN multiple action buttons are present THEN the system SHALL maintain consistent spacing and alignment
4. WHEN the button is in loading state THEN the system SHALL show a spinner icon and "Posting..." text

### Requirement 5

**User Story:** As a developer, I want the posting functionality to integrate with existing backend endpoints, so that the feature works consistently with the current architecture.

#### Acceptance Criteria

1. WHEN implementing the feature THEN the system SHALL use the existing `/posts/{post_id}/publish` endpoint
2. WHEN the backend returns an error THEN the system SHALL handle the error gracefully and update the UI accordingly
3. WHEN the post is successfully published THEN the system SHALL trigger the existing post update callback to refresh the UI
4. WHEN making API calls THEN the system SHALL follow the existing error handling patterns used in other post operations