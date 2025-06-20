"""
Authentication service containing business logic for user management.
Integrates Supabase auth with local database operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import User, UserSession
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.utils.supabase import supabase_client


class AuthService:
    """
    Authentication service providing business logic for user management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sign_up(
        self, user_data: UserCreate, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user with Supabase and create local user record.

        Args:
            user_data: User registration data
            redirect_to: Optional redirect URL after email confirmation

        Returns:
            Dict containing user and token information
        """
        try:
            # Check if user already exists locally
            existing_user = await self._get_user_by_email(user_data.email)
            if existing_user:
                return {
                    "error": "User with this email already exists",
                    "user": None,
                    "tokens": None,
                }

            # Create user in Supabase
            supabase_response = await supabase_client.sign_up(
                email=user_data.email,
                password=user_data.password,
                redirect_to=redirect_to,
            )

            if supabase_response["error"]:
                return {
                    "error": supabase_response["error"],
                    "user": None,
                    "tokens": None,
                }

            supabase_user = supabase_response["user"]
            if not supabase_user:
                return {
                    "error": "Failed to create user in Supabase",
                    "user": None,
                    "tokens": None,
                }

            # Create local user record
            local_user = User(
                supabase_user_id=str(supabase_user.id),
                email=user_data.email,
                full_name=user_data.full_name,
                preferred_language=user_data.preferred_language,
                timezone=user_data.timezone,
                is_verified=supabase_user.email_confirmed_at is not None,
            )

            self.db.add(local_user)
            await self.db.commit()
            await self.db.refresh(local_user)

            # Create tokens if user is already confirmed
            tokens = None
            if supabase_response["session"]:
                tokens = await self._create_tokens(local_user)
                await self._create_session(
                    local_user.id, tokens.access_token, tokens.refresh_token
                )

            logger.info(f"User registered successfully: {user_data.email}")

            return {
                "error": None,
                "user": UserResponse.model_validate(
                    {**local_user.__dict__, "id": str(local_user.id)}
                ),
                "tokens": tokens,
                "message": "User registered successfully. Please check your email for verification.",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Sign up failed for {user_data.email}: {e}")
            return {"error": "Registration failed", "user": None, "tokens": None}

    async def sign_in(self, login_data: UserLogin) -> Dict[str, Any]:
        """
        Sign in a user with email and password.

        Args:
            login_data: User login credentials

        Returns:
            Dict containing user and token information
        """
        try:
            # Authenticate with Supabase
            supabase_response = await supabase_client.sign_in(
                email=login_data.email, password=login_data.password
            )

            if supabase_response["error"]:
                return {
                    "error": supabase_response["error"],
                    "user": None,
                    "tokens": None,
                }

            supabase_user = supabase_response["user"]
            if not supabase_user:
                return {"error": "Authentication failed", "user": None, "tokens": None}

            # Get or create local user record
            local_user = await self._get_user_by_supabase_id(str(supabase_user.id))
            if not local_user:
                # Create local user if doesn't exist
                local_user = User(
                    supabase_user_id=str(supabase_user.id),
                    email=login_data.email,
                    is_verified=supabase_user.email_confirmed_at is not None,
                )
                self.db.add(local_user)
                await self.db.commit()
                await self.db.refresh(local_user)

            # Update last login
            await self._update_last_login(local_user.id)

            # Create tokens and session
            tokens = await self._create_tokens(local_user)
            await self._create_session(
                local_user.id, tokens.access_token, tokens.refresh_token
            )

            logger.info(f"User signed in successfully: {login_data.email}")

            return {
                "error": None,
                "user": UserResponse.model_validate(
                    {**local_user.__dict__, "id": str(local_user.id)}
                ),
                "tokens": tokens,
                "message": "Sign in successful",
            }

        except Exception as e:
            logger.error(f"Sign in failed for {login_data.email}: {e}")
            return {"error": "Sign in failed", "user": None, "tokens": None}

    async def sign_in_with_google(
        self, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate Google OAuth sign in.

        Args:
            redirect_to: Optional redirect URL after authentication

        Returns:
            Dict containing OAuth URL
        """
        try:
            response = await supabase_client.sign_in_with_oauth(
                provider="google", redirect_to=redirect_to
            )

            if response["error"]:
                return {"error": response["error"], "url": None}

            logger.info("Google OAuth sign in initiated")

            return {
                "error": None,
                "url": response["url"],
                "message": "OAuth sign in initiated",
            }

        except Exception as e:
            logger.error(f"Google OAuth sign in failed: {e}")
            return {"error": "OAuth sign in failed", "url": None}

    async def exchange_code_for_session(self, code: str) -> Dict[str, Any]:
        """
        Exchanges an authorization code from a Supabase OAuth callback for a user session.

        This is the core of the server-side OAuth flow. It also handles creating a
        local user record if one doesn't already exist for the Supabase user.

        Args:
            code: The authorization code provided by Supabase.

        Returns:
            A dictionary containing the user, tokens, and any potential error.
        """
        try:
            # Exchange the code for a Supabase session
            supabase_response = await supabase_client.exchange_code_for_session(code)

            if "error" in supabase_response:
                logger.error(
                    f"Supabase code exchange failed: {supabase_response['error']}"
                )
                return {
                    "error": supabase_response.get(
                        "error_description", "Invalid auth code"
                    )
                }

            supabase_user = supabase_response.get("user")
            supabase_session = supabase_response.get("session")

            if not supabase_user or not supabase_session:
                return {"error": "Failed to get user or session from Supabase."}

            # We have a valid Supabase user, find or create their local record
            local_user = await self._get_user_by_supabase_id(str(supabase_user.id))

            if not local_user:
                # User exists in Supabase but not locally, so create a local record
                user_metadata = supabase_user.user_metadata or {}
                local_user = User(
                    supabase_user_id=str(supabase_user.id),
                    email=supabase_user.email,
                    full_name=user_metadata.get("full_name", "New User"),
                    is_verified=supabase_user.email_confirmed_at is not None,
                )
                self.db.add(local_user)
                await self.db.commit()
                await self.db.refresh(local_user)
                logger.info(
                    f"Created new local user {local_user.email} from Google OAuth."
                )

            # Update last login time
            await self._update_last_login(local_user.id)

            # Create a session record in our local database
            await self._create_session(
                user_id=local_user.id,
                access_token=supabase_session.access_token,
                refresh_token=supabase_session.refresh_token,
            )

            # Prepare the token response
            tokens = TokenResponse(
                access_token=supabase_session.access_token,
                refresh_token=supabase_session.refresh_token,
                expires_in=supabase_session.expires_in or 3600,
            )

            return {
                "error": None,
                "user": UserResponse.model_validate(
                    {**local_user.__dict__, "id": str(local_user.id)}
                ),
                "tokens": tokens,
            }
        except Exception as e:
            await self.db.rollback()
            logger.opt(exception=True).error(
                f"Unexpected error during code exchange: {e}"
            )
            return {"error": "An internal server error occurred."}

    async def sign_out(self, access_token: str) -> Dict[str, Any]:
        """
        Sign out a user and revoke their session.

        Args:
            access_token: User's access token

        Returns:
            Dict indicating success or failure
        """
        try:
            # Verify token and get user
            user_id = verify_token(access_token)
            if not user_id:
                return {"error": "Invalid token"}

            # Revoke session in database
            await self._revoke_session_by_token(access_token)

            # Sign out from Supabase
            await supabase_client.sign_out(access_token)

            logger.info(f"User signed out successfully: {user_id}")

            return {"error": None, "message": "Sign out successful"}

        except Exception as e:
            logger.error(f"Sign out failed: {e}")
            return {"error": "Sign out failed"}

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dict containing new tokens
        """
        try:
            # Verify refresh token
            user_id = verify_token(refresh_token, "refresh")
            if not user_id:
                return {"error": "Invalid refresh token", "tokens": None}

            # Get user
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active:
                return {"error": "User not found or inactive", "tokens": None}

            # Create new tokens
            tokens = await self._create_tokens(user)

            # Update session
            await self._update_session_tokens(
                user.id, tokens.access_token, tokens.refresh_token
            )

            logger.info(f"Token refreshed successfully for user: {user_id}")

            return {
                "error": None,
                "tokens": tokens,
                "message": "Token refreshed successfully",
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return {
                "error": "Token refresh failed",
                "tokens": None,
            }

    async def get_current_user(self, access_token: str) -> Optional[UserResponse]:
        """
        Get the current user from an access token.

        Verifies the token, retrieves the user from the database,
        and returns user information.

        Args:
            access_token: The user's JWT access token.

        Returns:
            UserResponse object if the token is valid, otherwise None.
        """
        try:
            user_id = verify_token(access_token)
            if not user_id:
                return None

            user = await self._get_user_by_id(user_id)
            if not user:
                return None

            return UserResponse.model_validate({**user.__dict__, "id": str(user.id)})

        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    # Private helper methods

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_supabase_id(self, supabase_user_id: str) -> Optional[User]:
        """Get user by Supabase user ID."""
        stmt = select(User).where(
            User.supabase_user_id == supabase_user_id, User.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def _create_session(
        self, user_id: str, access_token: str, refresh_token: str
    ) -> UserSession:
        """Create a new user session."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

        session = UserSession(
            user_id=user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        self.db.add(session)
        await self.db.commit()
        return session

    async def _update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _revoke_session_by_token(self, access_token: str) -> None:
        """Revoke a session by access token."""
        stmt = (
            update(UserSession)
            .where(UserSession.session_token == access_token)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _update_session_tokens(
        self, user_id: str, access_token: str, refresh_token: str
    ) -> None:
        """Update session tokens."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(
                session_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                last_used_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
