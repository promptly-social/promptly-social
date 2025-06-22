# Unipile LinkedIn Integration

This document explains the Unipile integration for LinkedIn authentication and posting, which provides an alternative to LinkedIn's native OAuth API.

## Overview

The application supports two methods for LinkedIn integration:

1. **Native LinkedIn OAuth** (default) - Direct integration with LinkedIn's API
2. **Unipile Integration** - Unified messaging API that supports LinkedIn and other platforms

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Feature flag to enable Unipile (defaults to false)
USE_UNIPILE_FOR_LINKEDIN=true

# Unipile configuration (required when USE_UNIPILE_FOR_LINKEDIN=true)
UNIPILE_DSN=your-unipile-subdomain
UNIPILE_ACCESS_TOKEN=your-unipile-access-token

# Native LinkedIn OAuth (required when USE_UNIPILE_FOR_LINKEDIN=false)
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
```

### Development Setup with Webhooks

**Important**: Unipile webhooks require a publicly accessible URL. For local development, you'll need to expose your localhost using a tunnel service.

#### Option 1: Using ngrok (Recommended)

1. Install ngrok: https://ngrok.com/download
2. Start your backend server: `python -m uvicorn app.main:app --reload --port 8000`
3. In another terminal, expose port 8000: `ngrok http 8000`
4. Update your `.env` file with the ngrok URL:
   ```bash
   BACKEND_URL=https://your-ngrok-id.ngrok-free.app
   ```
5. Restart your backend server

#### Option 2: Using a public development server

Deploy your backend to a public service like:

- Heroku
- Railway
- Render
- Google Cloud Run

### Unipile Setup

1. Sign up for a Unipile account at [unipile.com](https://unipile.com)
2. Get your DSN (subdomain) and access token from the dashboard
3. The webhook endpoint will be automatically configured: `https://your-domain.com/api/v1/profile/linkedin/unipile-callback`

### Native LinkedIn Setup

1. Create a LinkedIn app at [LinkedIn Developer Portal](https://developer.linkedin.com)
2. Configure OAuth redirect URI: `https://your-domain.com/auth/linkedin/callback`
3. Get your Client ID and Client Secret

## User Experience Differences

### Native LinkedIn OAuth Flow

1. User clicks "Connect LinkedIn"
2. New window opens with LinkedIn OAuth
3. User authorizes the application
4. LinkedIn redirects back to callback URL with authorization code
5. Backend exchanges code for access token
6. User sees success message

### Unipile Flow

1. User clicks "Connect LinkedIn"
2. New window opens with Unipile's hosted auth interface
3. User completes LinkedIn authentication through Unipile
4. Unipile sends webhook notification to backend (user may close window)
5. Frontend polls for connection status to detect successful authentication
6. User sees success message when connection is confirmed

**Important Notes for Unipile:**

- Users can close the auth window after completing authentication
- The frontend will detect the connection via polling (up to 30 seconds)
- If the window is closed without completing auth, users will see a helpful message
- The connection happens via webhook, so no redirect URL parameters are needed

## API Endpoints

### Get Authentication Info

```http
GET /api/v1/profile/linkedin/auth-info
```

Returns information about the current authentication method:

```json
{
  "auth_method": "unipile",
  "provider": "Unipile",
  "configured": true
}
```

### Get Authorization URL

```http
GET /api/v1/profile/linkedin/authorize
```

Returns the appropriate authorization URL based on the configured method:

**Native LinkedIn Response:**

```json
{
  "authorization_url": "https://www.linkedin.com/oauth/v2/authorization?..."
}
```

**Unipile Response:**

```json
{
  "authorization_url": "https://api.unipile.com/hosted/auth/xyz123..."
}
```

### Handle OAuth Callback (Native LinkedIn)

```http
GET /api/v1/profile/linkedin/callback?code=...&state=...
```

### Handle Unipile Webhook

```http
POST /api/v1/profile/linkedin/unipile-callback
```

Webhook payload from Unipile:

```json
{
  "status": "CREATION_SUCCESS",
  "account_id": "account_123",
  "name": "linkedin_oauth_state_user123"
}
```

### Share on LinkedIn

```http
POST /api/v1/profile/linkedin/share
Content-Type: application/json

{
  "text": "Hello LinkedIn!"
}
```

Response:

```json
{
  "share_id": "123456",
  "method": "unipile"
}
```

### Get Unipile Accounts (Debug)

```http
GET /api/v1/profile/linkedin/unipile-accounts
```

Only available when `USE_UNIPILE_FOR_LINKEDIN=true`.

## Frontend Integration

### React Component Usage

The `UnipileLinkedInConnection` component automatically detects the auth method and handles both flows:

```tsx
import { UnipileLinkedInConnection } from "@/components/UnipileLinkedInConnection";

function ProfilePage() {
  return (
    <UnipileLinkedInConnection
      onConnectionUpdate={(connection) => {
        console.log("LinkedIn connection updated:", connection);
      }}
    />
  );
}
```

### Manual API Usage

```typescript
import { profileApi } from "@/lib/profile-api";

// Check auth method
const authInfo = await profileApi.linkedinAuthInfo();

// Get auth URL
const authResponse = await profileApi.linkedinAuthorize();

// For native LinkedIn, handle callback
if (authInfo.auth_method === "native") {
  const connection = await profileApi.linkedinCallback(code, state);
}

// For Unipile, poll for connection status
if (authInfo.auth_method === "unipile") {
  // Open auth window, then poll:
  const connections = await profileApi.getSocialConnections();
  const linkedinConn = connections.find((c) => c.platform === "linkedin");
}

// Share content
await profileApi.shareOnLinkedIn("Hello from my app!");
```

## Migration Strategy

### From Native to Unipile

1. Set `USE_UNIPILE_FOR_LINKEDIN=true`
2. Configure Unipile credentials
3. Set up webhook endpoint
4. Existing native connections will continue to work
5. New connections will use Unipile

### From Unipile to Native

1. Set `USE_UNIPILE_FOR_LINKEDIN=false`
2. Configure LinkedIn OAuth credentials
3. Existing Unipile connections will continue to work
4. New connections will use native LinkedIn OAuth

## Troubleshooting

### Common Issues

**"Route Not Found" error with Unipile**

- Check that `UNIPILE_DSN` is correct (should be just the subdomain)
- Verify `UNIPILE_ACCESS_TOKEN` is valid
- Ensure webhook endpoint is accessible

**Authentication window closes without success**

- For Unipile: This is normal behavior - the frontend will poll for connection status
- Check webhook endpoint is receiving notifications
- Verify network connectivity for polling requests

**"Invalid authentication token" in API calls**

- Check that user is properly authenticated
- Verify JWT token is not expired
- Ensure user has proper permissions

**Webhook not receiving notifications**

- Verify webhook URL is publicly accessible
- Check that webhook endpoint is configured correctly in Unipile dashboard
- Test webhook endpoint manually

### Debug Endpoints

When `USE_UNIPILE_FOR_LINKEDIN=true`, you can use:

```bash
# Check Unipile accounts
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/profile/linkedin/unipile-accounts

# Check auth configuration
curl http://localhost:8000/api/v1/profile/linkedin/auth-info
```

### Logs

Monitor backend logs for:

- Unipile API errors
- Webhook processing
- Connection status updates
- Authentication flow steps

## Security Considerations

- Webhook endpoint should validate incoming requests
- Store minimal user data from both LinkedIn and Unipile
- Implement proper rate limiting
- Use HTTPS for all webhook endpoints
- Follow SOC-II and GDPR compliance standards

## Performance Notes

- Unipile handles token refresh automatically
- Native LinkedIn requires manual token refresh
- Webhook processing is asynchronous
- Frontend polling has built-in timeout (30 seconds)
- Connection status is cached in database

## Database Schema Changes

### New Connection Data Structure

All authentication data is now stored in the `connection_data` JSON field in the `social_connections` table. The old columns (`access_token`, `refresh_token`, `expires_at`, `scope`) have been removed.

#### Native LinkedIn Connection Structure

```json
{
  "auth_method": "native",
  "access_token": "linkedin_access_token",
  "refresh_token": "linkedin_refresh_token",
  "expires_at": "2024-12-31T23:59:59.999Z",
  "scope": "openid profile email w_member_social",
  "linkedin_user_id": "user_linkedin_id",
  "email": "user@example.com",
  "picture": "https://media.licdn.com/..."
}
```

#### Unipile Connection Structure

```json
{
  "auth_method": "unipile",
  "account_id": "unipile_account_123",
  "unipile_account_id": "unipile_account_123",
  "provider": "linkedin",
  "status": "connected",
  "webhook_status": "CREATION_SUCCESS",
  "webhook_data": {
    /* full webhook payload */
  }
}
```

### Migration

The migration automatically moves existing authentication data from the old columns into the `connection_data` JSON field:

```sql
-- Migrate existing data to connection_data JSON field
UPDATE social_connections
SET connection_data = COALESCE(connection_data, '{}'::jsonb) ||
    jsonb_build_object(
        'access_token', access_token,
        'refresh_token', refresh_token,
        'expires_at', expires_at::text,
        'scope', scope,
        'auth_method', COALESCE((connection_data->>'auth_method'), 'native')
    )
WHERE access_token IS NOT NULL OR refresh_token IS NOT NULL OR expires_at IS NOT NULL OR scope IS NOT NULL;

-- Drop old columns
ALTER TABLE social_connections
DROP COLUMN access_token,
DROP COLUMN refresh_token,
DROP COLUMN expires_at,
DROP COLUMN scope;
```
