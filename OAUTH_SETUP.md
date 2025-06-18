# Google OAuth Setup Guide

This guide explains how to set up Google OAuth authentication for the Promptly application.

## Backend Setup

### 1. Google Cloud Console Configuration

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google Identity API
4. Go to "Credentials" in the sidebar
5. Click "Create Credentials" → "OAuth 2.0 Client IDs"
6. Configure the OAuth consent screen:
   - Add your application name
   - Add authorized domains (e.g., `localhost`, your domain)
   - Add scopes: `email`, `profile`, `openid`
7. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Authorized JavaScript origins:
     - `http://localhost:3000` (development)
     - `https://yourdomain.com` (production)
   - Authorized redirect URIs:
     - `http://localhost:8000/auth/callback/google` (development)
     - `https://yourapi.com/auth/callback/google` (production)

### 2. Environment Variables

Copy the credentials to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_actual_google_client_id
GOOGLE_CLIENT_SECRET=your_actual_google_client_secret
```

### 3. Supabase Configuration

1. Go to your Supabase dashboard
2. Navigate to Authentication → Providers
3. Enable Google provider
4. Add your Google OAuth credentials:
   - Client ID: Your Google Client ID
   - Client Secret: Your Google Client Secret
5. Set redirect URL: `http://localhost:8000/auth/callback/google`

## Frontend Setup

The frontend is already configured to work with the OAuth flow. The main components are:

- **Login Page**: Contains the "Continue with Google" button
- **OAuth Callback Page**: Handles the authentication response
- **Auth Context**: Manages authentication state

## OAuth Flow

1. User clicks "Continue with Google" on login page
2. Frontend calls `/auth/signin/google` endpoint
3. Backend generates Google OAuth URL via Supabase
4. User is redirected to Google for authentication
5. Google redirects back to `/auth/callback/google` with authorization code
6. Backend exchanges code for user session via Supabase
7. Backend redirects to frontend with authentication tokens
8. Frontend OAuth callback page processes tokens and updates auth state

## API Endpoints

### Initiate Google OAuth

```http
POST /auth/signin/google
Content-Type: application/json

{
  "redirect_to": "http://localhost:3000/new-content"
}
```

### OAuth Callback (handled automatically)

```http
GET /auth/callback/google?code=<auth_code>&state=<state>
```

### Sign in with Google ID Token (alternative)

```http
POST /auth/signin/google/token
Content-Type: application/json

{
  "id_token": "<google_id_token>",
  "redirect_to": "http://localhost:3000/new-content"
}
```

## Testing

1. Start the backend server: `cd backend && uvicorn app.main:app --reload`
2. Start the frontend server: `cd frontend && npm run dev`
3. Navigate to `http://localhost:3000/login`
4. Click "Continue with Google"
5. Complete the OAuth flow

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure your frontend URL is in CORS_ORIGINS
2. **Redirect URI Mismatch**: Check Google Console redirect URIs match your backend
3. **Invalid Client ID**: Verify credentials in environment variables
4. **Supabase Auth Issues**: Check Supabase provider configuration

### Debug Logs

The backend logs OAuth events. Check the console for:

- `Initiating google OAuth sign in`
- `Google OAuth URL generated successfully`
- `OAuth callback successful`

## Security Considerations

- Always use HTTPS in production
- Validate redirect URLs on the backend
- Use secure token storage
- Implement proper session management
- Add rate limiting to OAuth endpoints

## Dependencies

The implementation uses:

- **Backend**: FastAPI, Supabase Python client
- **Frontend**: React Router, custom auth context
- **Authentication**: Supabase Auth with Google provider
