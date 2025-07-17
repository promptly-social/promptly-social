# Implementation Plan

- [x] 1. Update backend Post model and database schema

  - Add sharing_error column to posts table with database migration
  - Update Post model in backend/app/models/posts.py to include sharing_error field
  - Update PostResponse schema in backend/app/schemas/posts.py to include sharing_error field
  - _Requirements: 2.2, 3.4_

- [x] 2. Enhance backend publish endpoint error handling

  - Modify publish_post method in backend/app/services/posts.py to handle sharing_error updates
  - Ensure sharing_error is cleared on successful publish and populated on failure
  - Update posts router publish endpoint to properly handle error responses
  - _Requirements: 2.1, 2.2, 2.3, 5.2_

- [x] 3. Update frontend Post type definition

  - Add sharing_error field to Post interface in frontend/src/types/posts.ts
  - Ensure the field is properly typed as optional string
  - _Requirements: 3.1, 5.1_

- [x] 4. Add postNow method to posts API client

  - Create postNow method in frontend/src/lib/posts-api.ts that calls the publish endpoint
  - Implement proper error handling and response typing
  - Follow existing API patterns for authentication and error handling
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 5. Create error indicator component

  - Implement PostSharingError component to display error indicators
  - Add warning icon and user-friendly error message tooltip
  - Style component to be non-intrusive but clearly visible
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 6. Enhance PostCardActions component

  - Add "Post Now" button with proper conditional rendering logic
  - Implement loading state with spinner and "Posting..." text
  - Add postingPostId prop and onPostNow callback to component interface
  - Position button appropriately based on post status
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.3, 4.4_

- [x] 7. Update PostCard component with posting functionality

  - Add posting state management and postNow handler method
  - Implement API call with proper loading states and error handling
  - Add success/error toast notifications
  - Integrate error indicator display for posts with sharing_error
  - Ensure post data refresh after posting operations
  - _Requirements: 1.3, 1.4, 2.3, 2.4, 3.1, 5.3_

- [x] 8. Write comprehensive tests for new functionality
  - Create unit tests for PostCardActions component with new button
  - Add tests for PostCard posting functionality and error handling
  - Test API client postNow method with success/error scenarios
  - Write integration tests for complete posting flow
  - _Requirements: All requirements validation through testing_
