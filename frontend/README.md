# Frontend - Social Scribe

This is the React frontend application for Social Scribe, built with Vite, TypeScript, and Tailwind CSS.

## Setup

1. Install dependencies:

```bash
npm install
```

2. Create a `.env` file in the frontend directory with the following variables:

```env
# Backend API Configuration
VITE_API_URL=http://localhost:8000

# Optional: Enable development mode
VITE_NODE_ENV=development
```

3. Start the development server:

```bash
npm run dev
```

## Authentication

The frontend now uses the Python FastAPI backend for authentication instead of Supabase directly. The authentication system includes:

- **Sign Up**: Create new user accounts with email/password
- **Sign In**: Authenticate users with email/password
- **Google OAuth**: Sign in with Google account
- **Token Management**: Automatic token refresh and secure storage
- **Protected Routes**: Automatic authentication checking

### Key Features

- **Automatic Token Refresh**: Tokens are automatically refreshed before expiration
- **Secure Storage**: Tokens are stored in localStorage with expiration tracking
- **Error Handling**: Graceful handling of authentication errors with automatic logout
- **Type Safety**: Full TypeScript support with proper type definitions

## API Integration

The frontend communicates with the backend through:

- `/auth/signup` - User registration
- `/auth/signin` - User authentication
- `/auth/signin/google` - Google OAuth initiation
- `/auth/signout` - User logout
- `/auth/refresh` - Token refresh
- `/auth/me` - Get current user info

## Development

The AuthContext now manages authentication state and provides:

```typescript
interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (
    email: string,
    password: string,
    fullName?: string
  ) => Promise<{ error: Error | null }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signInWithGoogle: () => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  refreshAuthToken: () => Promise<boolean>;
}
```

## Environment Variables

| Variable        | Description          | Default                 |
| --------------- | -------------------- | ----------------------- |
| `VITE_API_URL`  | Backend API base URL | `http://localhost:8000` |
| `VITE_NODE_ENV` | Development mode     | `development`           |

Make sure your backend is running on the configured URL before starting the frontend.
