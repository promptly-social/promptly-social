"""
Supabase client wrapper with enhanced error handling and logging.
Provides a centralized interface for all Supabase operations.
"""

from typing import Optional, Dict, Any
from loguru import logger
from supabase import create_client, Client

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
            self._client = create_client(self.url, self.key)
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

    def sign_in_with_google(self, id_token: str) -> Dict[str, Any]:
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


def get_supabase_client() -> SupabaseClient:
    """Get Supabase client instance."""
    return SupabaseClient()


# Global instance - will be initialized lazily
supabase_client = SupabaseClient()
