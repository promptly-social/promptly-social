# Design Document

## Overview

The "Post Now" feature extends the existing PostCardActions component to include immediate LinkedIn publishing functionality. The design leverages the existing backend API endpoint and follows established patterns for error handling, loading states, and user feedback within the application.

## Architecture

### Component Structure
- **PostCardActions**: Enhanced to include the "Post Now" button with conditional rendering logic
- **PostCard**: Updated to handle posting operations and display error indicators
- **Backend Integration**: Utilizes existing `/posts/{post_id}/publish` endpoint
- **State Management**: Integrates with existing post update mechanisms

### Data Flow
1. User clicks "Post Now" button
2. Frontend sends POST request to `/posts/{post_id}/publish?platform=linkedin`
3. Backend processes the request and attempts to publish to LinkedIn
4. Backend returns success/failure response
5. Frontend updates UI based on response (success toast, error handling, post refresh)

## Components and Interfaces

### PostCardActions Component Enhancement

```typescript
interface PostCardActionsProps {
  post: Post;
  savingPostId?: string | null;
  dismissingPostId?: string | null;
  postingPostId?: string | null; // New prop for posting state
  onSchedulePost?: (postId: string) => void;
  onRemoveFromSchedule?: (post: Post) => void;
  onReschedulePost?: (postId: string) => void;
  onSaveForLater?: (post: Post) => void;
  onDismissPost?: (post: Post) => void;
  onPostNow?: (post: Post) => void; // New callback for posting
}
```

### Post Type Extension

The existing Post type should include the sharing_error field:

```typescript
interface Post {
  // ... existing fields
  sharing_error?: string | null;
}
```

### Error Indicator Component

A new component to display sharing errors:

```typescript
interface PostSharingErrorProps {
  hasError: boolean;
}
```

## Data Models

### Database Schema Update
The posts table should include a `sharing_error` column:
- Type: TEXT (nullable)
- Purpose: Store error messages from failed publishing attempts
- Cleared when post is successfully published

### API Response Handling
The publish endpoint responses will be handled as follows:
- **Success**: Update post status to "posted", clear sharing_error
- **Error**: Maintain current status, populate sharing_error field

## Error Handling

### Frontend Error Handling
1. **Network Errors**: Display generic error toast, maintain button state
2. **API Errors**: Display error toast with backend message, update post with sharing_error
3. **Timeout Errors**: Display timeout message, allow retry

### Backend Error Handling
The existing `/posts/{post_id}/publish` endpoint already handles:
- Post not found (404)
- Publishing failures (500 with error details)
- Platform-specific errors

### Error Display Strategy
- **Error Indicator**: Small warning icon next to post metadata
- **Error Message**: User-friendly text without technical details
- **Error Tooltip**: "An error occurred when Promptly tried to post on your behalf. Please try to reschedule it or post it now"

## Testing Strategy

### Unit Tests
1. **PostCardActions Component**:
   - Renders "Post Now" button for appropriate post statuses
   - Handles loading states correctly
   - Calls onPostNow callback with correct parameters
   - Displays error indicators when sharing_error exists

2. **PostCard Component**:
   - Manages posting state correctly
   - Handles API success/error responses
   - Updates post data after operations
   - Displays appropriate toast messages

### Integration Tests
1. **API Integration**:
   - Successful post publishing flow
   - Error handling for various failure scenarios
   - Proper state management during async operations

2. **User Experience**:
   - Button states transition correctly
   - Error indicators appear/disappear appropriately
   - Toast notifications display correct messages

### Error Scenario Tests
1. Network connectivity issues
2. LinkedIn API failures
3. Authentication/authorization errors
4. Post content validation errors
5. Rate limiting scenarios

## Implementation Notes

### Button Positioning
The "Post Now" button will be positioned:
- For scheduled posts: Between "Remove from Schedule" and "Delete" buttons
- For draft posts: As the primary action button, styled with green background
- For suggested posts: After feedback section, before other actions

### Loading State Design
- Button text changes to "Posting..."
- Spinner icon replaces the normal icon
- Button becomes disabled during operation
- Other action buttons remain enabled (except conflicting actions)

### Error Indicator Design
- Small warning triangle icon with orange/red color
- Positioned near post metadata or timestamp
- Tooltip/hover text with user-friendly error message
- Non-intrusive but clearly visible

### State Management
- Posting state managed at PostCard level
- Error state derived from post.sharing_error field
- Loading states prevent multiple simultaneous operations
- Post refresh triggered after successful/failed operations