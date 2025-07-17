# Onboarding Workflow Implementation

## Overview

This document describes the comprehensive onboarding workflow implementation for new users in the Promptly Social Scribe application. The onboarding system guides users through 6 key steps to set up their account and understand the platform's features.

## Architecture

### Backend Components

#### Models
- **UserOnboarding** (`backend/app/models/onboarding.py`)
  - Tracks user onboarding progress
  - Stores completion status for each step
  - Supports skipping and resetting onboarding
  - Includes audit logging with timestamps

#### Database Schema
- **user_onboarding** table with the following key fields:
  - `user_id`: Foreign key to auth.users
  - `is_completed`: Overall completion status
  - `is_skipped`: Whether user skipped onboarding
  - `step_*_completed`: Individual step completion flags
  - `current_step`: Current step number (1-6)
  - `notes`: Optional user feedback
  - Audit fields: `created_at`, `updated_at`, `completed_at`, `skipped_at`

#### API Endpoints
- **OnboardingService** (`backend/app/services/onboarding_service.py`)
  - Business logic for onboarding operations
  - CRUD operations for onboarding progress
  - Step completion tracking and validation

- **Onboarding Router** (`backend/app/routers/onboarding.py`)
  - RESTful API endpoints:
    - `GET /api/v1/onboarding/` - Get progress
    - `POST /api/v1/onboarding/step` - Update step
    - `POST /api/v1/onboarding/skip` - Skip onboarding
    - `PUT /api/v1/onboarding/` - Update progress
    - `POST /api/v1/onboarding/reset` - Reset progress
    - `DELETE /api/v1/onboarding/` - Delete progress

### Frontend Components

#### Core Components
- **OnboardingProvider** (`frontend/src/components/onboarding/OnboardingProvider.tsx`)
  - Central state management for onboarding
  - Context provider for onboarding functionality
  - Auto-shows modal for new users

- **OnboardingModal** (`frontend/src/components/onboarding/OnboardingModal.tsx`)
  - Interactive step-by-step tour
  - Progress tracking and navigation
  - Skip functionality

- **OnboardingBanner** (`frontend/src/components/onboarding/OnboardingBanner.tsx`)
  - Contextual guidance on specific pages
  - Step-specific instructions and highlights
  - Dismissible with completion tracking

- **OnboardingProgress** (`frontend/src/components/onboarding/OnboardingProgress.tsx`)
  - Visual progress indicator
  - Compact and full view modes
  - Step navigation capabilities

#### Custom Hooks
- **useOnboarding** (`frontend/src/hooks/useOnboarding.ts`)
  - Manages onboarding state and API calls
  - Provides helper functions for step management
  - Handles navigation between steps

#### API Integration
- **onboardingApi** (`frontend/src/lib/api/onboarding.ts`)
  - API client for onboarding endpoints
  - Error handling and type safety
  - Consistent with existing API patterns

## Onboarding Steps

### Step 1: Profile Setup
**Page**: `/profile`
**Requirements**:
- Add LinkedIn handle (required)
- Connect Substack (optional)
- Click "Analyze" button to analyze writing style
- Analysis takes up to 5 minutes
- Analyzes: About Me, Writing Style, Topics of Interest
- Option to provide custom writing sample

### Step 2: Content Preferences
**Page**: `/content-preferences`
**Requirements**:
- Enter topics you like to write about
- Add news websites you follow
- Add Substack blogs you follow

### Step 3: Settings
**Page**: `/settings`
**Requirements**:
- Set daily suggestion time
- Generates 5 draft posts based on:
  - Articles from news sites
  - User bio and topics of interest

### Step 4: My Posts
**Page**: `/my-posts`
**Features**:
- "New Post" button for manual post creation
- "Brain Storm" button for AI-assisted drafting

### Step 5: Content Ideas
**Page**: `/idea-bank`
**Features**:
- Add notes for future content ideas
- Brainstorm drafts from saved ideas
- Note: URLs to social media platforms not supported yet

### Step 6: Posting Schedule
**Page**: `/posting-schedule`
**Features**:
- Review scheduled posts
- Manage posting calendar

## Implementation Details

### Database Migration
```sql
-- Migration: 20250717000000_create_user_onboarding_table.sql
CREATE TABLE user_onboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    is_skipped BOOLEAN NOT NULL DEFAULT FALSE,
    step_profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_content_preferences_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_settings_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_my_posts_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_content_ideas_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_posting_schedule_completed BOOLEAN NOT NULL DEFAULT FALSE,
    current_step INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    skipped_at TIMESTAMPTZ
);
```

### Usage Examples

#### Backend Usage
```python
from app.services.onboarding_service import OnboardingService

# Get or create onboarding progress
onboarding = OnboardingService.get_or_create_user_onboarding(db, user_id)

# Update a step
onboarding = OnboardingService.update_onboarding_step(db, user_id, step=1, completed=True)

# Skip onboarding
onboarding = OnboardingService.skip_onboarding(db, user_id, notes="User preference")
```

#### Frontend Usage
```tsx
import { OnboardingProvider, OnboardingBanner } from '@/components/onboarding';

// Wrap app with provider
<OnboardingProvider>
  <App />
</OnboardingProvider>

// Add banner to specific pages
<OnboardingBanner stepId={1} />
```

## Security & Compliance

### Row Level Security (RLS)
- Users can only access their own onboarding data
- Policies enforce user isolation
- Secure API endpoints with authentication

### Audit Logging
- All onboarding actions are logged with timestamps
- Tracks creation, updates, completion, and skipping
- Follows SOC-II and GDPR standards

### Data Privacy
- Optional notes field for user feedback
- Soft delete capability
- User can reset or delete onboarding data

## Testing

### Backend Tests
- Unit tests for OnboardingService methods
- API endpoint testing
- Database operation validation
- Error handling verification

### Frontend Tests
- Hook functionality testing
- Component rendering tests
- API integration testing
- User interaction simulation

## Deployment Considerations

### Database
- Migration must be applied before deployment
- Indexes created for performance
- RLS policies enabled for security

### Frontend
- Components are lazy-loaded where possible
- Progressive enhancement approach
- Responsive design for all screen sizes

### Monitoring
- Track onboarding completion rates
- Monitor step abandonment points
- Log API errors and performance metrics

## Future Enhancements

### Potential Improvements
1. **Analytics Dashboard**: Track onboarding metrics and user behavior
2. **A/B Testing**: Test different onboarding flows
3. **Personalization**: Customize onboarding based on user type
4. **Interactive Tutorials**: Add interactive elements to guide users
5. **Progress Persistence**: Save progress across sessions
6. **Notification System**: Remind users to complete onboarding

### Technical Debt
- Consider moving to a more sophisticated state machine for complex flows
- Implement caching for onboarding data
- Add more granular error handling and recovery

## Troubleshooting

### Common Issues
1. **Onboarding not showing**: Check user authentication and API connectivity
2. **Steps not updating**: Verify backend API endpoints are accessible
3. **Modal not appearing**: Check OnboardingProvider configuration
4. **Progress not persisting**: Verify database connection and RLS policies

### Debug Tools
- Browser console for frontend errors
- Backend logs for API issues
- Database queries for data verification
- Network tab for API call inspection

## Conclusion

The onboarding workflow provides a comprehensive introduction to the Promptly Social Scribe platform while maintaining flexibility for users who prefer to skip the guided experience. The implementation follows best practices for both backend and frontend development, ensuring scalability, security, and maintainability.
