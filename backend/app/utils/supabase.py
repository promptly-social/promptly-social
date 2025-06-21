"""
Supabase client wrapper with enhanced error handling and logging.
Provides a centralized interface for all Supabase operations.
"""

from typing import Any, Dict, Optional

from loguru import logger
from supabase import Client, create_client

from app.core.config import settings


class SupabaseClient:
    """
    Wrapper class for Supabase client with enhanced error handling.

    Provides centralized logging, error handling, and retry logic
    for all Supabase operations.
    """

    def __init__(self):
        """Initialize Supabase client wrapper."""
        self._client: Optional[Client] = None
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        self.service_key = settings.supabase_service_key

    @property
    def client(self) -> Client:
        """Lazy initialization of Supabase client."""
        if self._client is None:
            from gotrue import SyncMemoryStorage
            from supabase.lib.client_options import ClientOptions

            # Configure client for server-side auth flow
            options = ClientOptions(
                storage=SyncMemoryStorage(),
                auto_refresh_token=False,
                persist_session=False,
            )
            self._client = create_client(self.url, self.key, options)
        return self._client

    async def sign_up(self, email: str, password: str, **kwargs) -> Dict[str, Any]:
        """
        Sign up a new user with email and password.

        Args:
            email: User's email address
            password: User's password
            **kwargs: Additional user data

        Returns:
            Dictionary containing user data, session, or error
        """
        try:
            logger.info(f"Attempting to sign up user: {email}")

            response = self.client.auth.sign_up(
                {"email": email, "password": password, "options": {"data": kwargs}}
            )

            if response.user:
                logger.info(f"User signed up successfully: {email}")
                return {
                    "user": response.user,
                    "session": response.session,
                    "error": None,
                }
            else:
                logger.warning(f"Sign up failed for user: {email}")
                return {"user": None, "session": None, "error": "Sign up failed"}

        except Exception as e:
            logger.error(f"Sign up error for {email}: {str(e)}")
            return {"user": None, "session": None, "error": str(e)}

    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dictionary containing user data, session, or error
        """
        try:
            logger.info(f"Attempting to sign in user: {email}")

            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if response.user and response.session:
                logger.info(f"User signed in successfully: {email}")
                return {
                    "user": response.user,
                    "session": response.session,
                    "error": None,
                }
            else:
                logger.warning(f"Sign in failed for user: {email}")
                return {"user": None, "session": None, "error": "Invalid credentials"}

        except Exception as e:
            logger.error(f"Sign in error for {email}: {str(e)}")
            return {"user": None, "session": None, "error": str(e)}

    async def sign_out(self, access_token: str) -> Dict[str, Any]:
        """
        Sign out user.

        Args:
            access_token: User's access token

        Returns:
            Dictionary containing success status or error
        """
        try:
            logger.info("Attempting to sign out user")

            # Set the session token
            self.client.auth.set_session(access_token, "")

            self.client.auth.sign_out()

            logger.info("User signed out successfully")
            return {"success": True, "error": None}

        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user data from access token.

        Args:
            access_token: User's access token

        Returns:
            Dictionary containing user data or error
        """
        try:
            # Set the session token
            self.client.auth.set_session(access_token, "")

            response = self.client.auth.get_user()

            if response.user:
                return {"user": response.user, "error": None}
            else:
                return {"user": None, "error": "Invalid token"}

        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return {"user": None, "error": str(e)}

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh user session with refresh token.

        Args:
            refresh_token: User's refresh token

        Returns:
            Dictionary containing new session or error
        """
        try:
            logger.info("Attempting to refresh token")

            response = self.client.auth.refresh_session(refresh_token)

            if response.session:
                logger.info("Token refreshed successfully")
                return {"session": response.session, "error": None}
            else:
                logger.warning("Token refresh failed")
                return {"session": None, "error": "Token refresh failed"}

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return {"session": None, "error": str(e)}

    def reset_password(self, email: str) -> Dict[str, Any]:
        """
        Send password reset email.

        Args:
            email: User's email address

        Returns:
            Dictionary containing success status or error
        """
        try:
            logger.info(f"Sending password reset email to: {email}")

            self.client.auth.reset_password_email(email)

            logger.info(f"Password reset email sent to: {email}")
            return {"success": True, "error": None}

        except Exception as e:
            logger.error(f"Password reset error for {email}: {str(e)}")
            return {"success": False, "error": str(e)}

    def update_user(self, access_token: str, **kwargs) -> Dict[str, Any]:
        """
        Update user data.

        Args:
            access_token: User's access token
            **kwargs: User data to update

        Returns:
            Dictionary containing updated user data or error
        """
        try:
            logger.info("Updating user data")

            # Set the session token
            self.client.auth.set_session(access_token, "")

            response = self.client.auth.update_user(kwargs)

            if response.user:
                logger.info("User data updated successfully")
                return {"user": response.user, "error": None}
            else:
                logger.warning("User data update failed")
                return {"user": None, "error": "Update failed"}

        except Exception as e:
            logger.error(f"User update error: {str(e)}")
            return {"user": None, "error": str(e)}

    async def sign_in_with_oauth(
        self, provider: str, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate OAuth sign in flow.

        Args:
            provider: OAuth provider (e.g., 'google')
            redirect_to: Optional redirect URL after authentication

        Returns:
            Dictionary containing OAuth URL or error
        """
        try:
            logger.info(f"Initiating {provider} OAuth sign in")
            logger.info(f"Final redirect to: {redirect_to}")

            # Configure Supabase to redirect to our backend callback, not directly to frontend
            backend_callback_url = (
                f"{settings.backend_url}/api/v1/auth/callback/{provider}"
            )
            if redirect_to:
                backend_callback_url += f"?redirect_to={redirect_to}"

            logger.info(f"Backend callback URL: {backend_callback_url}")

            oauth_options = {
                "provider": provider,
                "options": {"redirectTo": backend_callback_url},
            }
            logger.info(f"OAuth options being sent to Supabase: {oauth_options}")

            response = self.client.auth.sign_in_with_oauth(oauth_options)

            if response.url:
                logger.info(f"{provider} OAuth URL generated successfully")
                logger.info(f"Generated OAuth URL: {response.url}")
                return {
                    "url": response.url,
                    "error": None,
                }
            else:
                logger.warning(f"{provider} OAuth URL generation failed")
                return {"url": None, "error": f"{provider} OAuth failed"}

        except Exception as e:
            logger.error(f"{provider} OAuth error: {str(e)}")
            return {"url": None, "error": str(e)}

    async def handle_oauth_callback(
        self, code: str, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for session.

        Args:
            code: OAuth authorization code
            redirect_to: Optional redirect URL

        Returns:
            Dictionary containing user data, session, or error
        """
        try:
            logger.info(f"Handling OAuth callback with code: {code[:20]}...")

            response = self.client.auth.exchange_code_for_session({"auth_code": code})

            if response.user and response.session:
                logger.info(f"OAuth callback successful: {response.user.email}")
                return {
                    "user": response.user,
                    "session": response.session,
                    "error": None,
                }
            else:
                logger.warning("OAuth callback failed - no user or session in response")
                return {
                    "user": None,
                    "session": None,
                    "error": "OAuth authentication failed",
                }

        except Exception as e:
            logger.error(f"OAuth callback exception: {str(e)}")
            return {
                "user": None,
                "session": None,
                "error": f"OAuth exchange failed: {str(e)}",
            }

    def sign_in_with_google_token(self, id_token: str) -> Dict[str, Any]:
        """
        Sign in user with Google OAuth.

        Args:
            id_token: Google ID token

        Returns:
            Dictionary containing user data, session, or error
        """
        try:
            logger.info("Attempting Google OAuth sign in")

            response = self.client.auth.sign_in_with_id_token(
                {"provider": "google", "token": id_token}
            )

            if response.user and response.session:
                logger.info(f"Google OAuth sign in successful: {response.user.email}")
                return {
                    "user": response.user,
                    "session": response.session,
                    "error": None,
                }
            else:
                logger.warning("Google OAuth sign in failed")
                return {"user": None, "session": None, "error": "Google OAuth failed"}

        except Exception as e:
            logger.error(f"Google OAuth error: {str(e)}")
            return {"user": None, "session": None, "error": str(e)}

    def _create_user_from_response(self, data: Dict[str, Any]) -> Any:
        """
        Create a user object from Supabase token response.

        Args:
            data: Token response data from Supabase

        Returns:
            User object compatible with Supabase auth
        """
        try:
            from types import SimpleNamespace

            user_data = data.get("user", {})

            # Create a simple user object with the expected attributes
            user = SimpleNamespace()
            user.id = user_data.get("id")
            user.email = user_data.get("email")
            user.email_confirmed_at = user_data.get("email_confirmed_at")
            user.phone = user_data.get("phone")
            user.confirmed_at = user_data.get("confirmed_at")
            user.last_sign_in_at = user_data.get("last_sign_in_at")
            user.app_metadata = user_data.get("app_metadata", {})
            user.user_metadata = user_data.get("user_metadata", {})
            user.identities = user_data.get("identities", [])
            user.created_at = user_data.get("created_at")
            user.updated_at = user_data.get("updated_at")

            logger.info(f"Created user object for: {user.email}")
            return user

        except Exception as e:
            logger.error(f"Error creating user from response: {e}")
            return None

    def _create_session_from_response(self, data: Dict[str, Any]) -> Any:
        """
        Create a session object from Supabase token response.

        Args:
            data: Token response data from Supabase

        Returns:
            Session object compatible with Supabase auth
        """
        try:
            from types import SimpleNamespace

            # Create a simple session object with the expected attributes
            session = SimpleNamespace()
            session.access_token = data.get("access_token")
            session.refresh_token = data.get("refresh_token")
            session.expires_in = data.get("expires_in")
            session.expires_at = data.get("expires_at")
            session.token_type = data.get("token_type", "bearer")
            session.user = self._create_user_from_response(data)

            logger.info("Created session object")
            return session

        except Exception as e:
            logger.error(f"Error creating session from response: {e}")
            return None


def get_supabase_client() -> SupabaseClient:
    """Get Supabase client instance."""
    return SupabaseClient()


# Global instance - will be initialized lazily
supabase_client = SupabaseClient()
