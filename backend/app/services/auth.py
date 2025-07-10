"""
Authentication service containing business logic for user management.
Integrates Supabase auth with local database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from loguru import logger

from app.models.user import User, UserSession
from app.models.idea_bank import IdeaBank
from app.models.posts import Post
from app.models.profile import SocialConnection, UserPreferences, WritingStyleAnalysis
from app.models.content_strategies import ContentStrategy
from app.models.daily_suggestion_schedule import DailySuggestionSchedule
from app.models.chat import Conversation
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    UserUpdate,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.config import settings
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

            # Create user in Supabase with redirect to backend verification endpoint
            backend_redirect_url = f"{settings.backend_url}/api/v1/auth/verify"

            supabase_response = await supabase_client.sign_up(
                email=user_data.email,
                password=user_data.password,
                redirect_to=backend_redirect_url,
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

            # Don't create tokens for email signup - user needs to verify email first
            tokens = None
            # Only create tokens if user is already confirmed (which shouldn't happen with email signup)
            if supabase_response["session"] and supabase_user.email_confirmed_at:
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
                logger.info(
                    f"Created new local user: {login_data.email}, is_verified: {local_user.is_verified}"
                )
            else:
                logger.info(
                    f"Found existing local user: {login_data.email}, is_verified: {local_user.is_verified}"
                )

            # Update last login
            await self._update_last_login(local_user.id)

            # Create tokens and session
            tokens = await self._create_tokens(local_user)
            await self._create_session(
                local_user.id, tokens.access_token, tokens.refresh_token
            )

            logger.info(f"User signed in successfully: {login_data.email}")

            user_response = UserResponse.model_validate(
                {**local_user.__dict__, "id": str(local_user.id)}
            )
            logger.info(f"Returning user data: {user_response.model_dump()}")

            return {
                "error": None,
                "user": user_response,
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

    async def delete_account(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user's account and all associated data.

        Args:
            user_id: The ID of the user to delete.

        Returns:
            Dict indicating success or failure.
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            return {"error": "User not found", "success": False}

        try:
            logger.info(f"Starting account deletion for user_id: {user_id}")

            # Delete related data. Order doesn't strictly matter here but it's good practice
            # to delete child objects before parent objects if there are dependencies without ON DELETE CASCADE.
            # In our case, we are deleting everything related to a user.

            # These models have a direct relationship with the user.
            # The order matters here due to foreign key constraints that are not set to cascade on delete.
            # Specifically, Posts and Conversations must be deleted before IdeaBanks.
            models_to_delete = [
                Post,
                Conversation,
                IdeaBank,
                SocialConnection,
                UserPreferences,
                WritingStyleAnalysis,
                ContentStrategy,
                DailySuggestionSchedule,
                UserSession,
            ]

            for model in models_to_delete:
                stmt = delete(model).where(model.user_id == user.id)
                await self.db.execute(stmt)
                logger.info(f"Deleted {model.__tablename__} for user_id: {user_id}")

            # Now delete the user from public.users
            await self.db.delete(user)
            logger.info(f"Deleted user object for user_id: {user_id}")

            # Finally, delete user from Supabase auth
            # This is last, so if it fails, the DB transaction can be rolled back.
            if user.supabase_user_id:
                supabase_response = await supabase_client.delete_user(
                    user.supabase_user_id
                )
                if supabase_response["error"]:
                    # This will trigger a rollback of the DB operations
                    raise Exception(
                        f"Supabase deletion failed: {supabase_response['error']}"
                    )

            await self.db.commit()
            logger.info(f"Successfully deleted account for user_id: {user_id}")
            return {"success": True, "error": None}

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Account deletion failed for {user_id}: {e}")
            return {"error": "Account deletion failed", "success": False}

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
                user.id,
                tokens.access_token,
                tokens.refresh_token,
                old_refresh_token=refresh_token,
            )

            logger.info(f"Token refreshed successfully for user: {user_id}")

            return {
                "error": None,
                "tokens": tokens,
                "message": "Token refreshed successfully",
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return {"error": "Token refresh failed", "tokens": None}

    async def get_current_user(self, access_token: str) -> Optional[UserResponse]:
        """
        Get current user from access token.

        Args:
            access_token: User's access token

        Returns:
            User information if token is valid
        """
        try:
            user_id = verify_token(access_token)
            if not user_id:
                return None

            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active:
                return None

            return UserResponse.model_validate({**user.__dict__, "id": str(user.id)})

        except Exception as e:
            logger.error(f"Get current user failed: {e}")
            return None

    async def update_user(
        self, user_id: str, user_data: UserUpdate
    ) -> Optional[UserResponse]:
        """
        Update user profile information.

        Args:
            user_id: User ID to update
            user_data: User update data

        Returns:
            Updated user information
        """
        try:
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active:
                return None

            # Update fields if provided
            update_data = user_data.model_dump(exclude_unset=True)

            # Handle password update if provided
            if "password" in update_data and "confirm_password" in update_data:
                if update_data["password"] != update_data["confirm_password"]:
                    raise ValueError("Passwords do not match")

                # Update password in Supabase if user has supabase_user_id
                if user.supabase_user_id:
                    from app.utils.supabase import supabase_client

                    supabase_result = await supabase_client.update_user(
                        user.supabase_user_id, password=update_data["password"]
                    )
                    if supabase_result.get("error"):
                        raise ValueError(
                            f"Failed to update password in Supabase: {supabase_result['error']}"
                        )

                # Remove password fields from update data
                update_data.pop("password", None)
                update_data.pop("confirm_password", None)

            # Update local user record
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"User profile updated successfully: {user_id}")
            return UserResponse.model_validate({**user.__dict__, "id": str(user.id)})

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Update user failed for {user_id}: {e}")
            raise

    async def handle_oauth_callback(
        self, code: str, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and create user session.

        Args:
            code: OAuth authorization code
            redirect_to: Optional redirect URL

        Returns:
            Dict containing user and token information
        """
        try:
            # Exchange code for session with Supabase
            supabase_response = await supabase_client.handle_oauth_callback(
                code, redirect_to
            )

            # Handle case where supabase_response might be a string
            if isinstance(supabase_response, str):
                return {
                    "error": supabase_response,
                    "user": None,
                    "tokens": None,
                }

            if not isinstance(supabase_response, dict):
                return {
                    "error": "Invalid response from Supabase",
                    "user": None,
                    "tokens": None,
                }

            if supabase_response.get("error"):
                return {
                    "error": supabase_response["error"],
                    "user": None,
                    "tokens": None,
                }

            supabase_user = supabase_response.get("user")
            if not supabase_user:
                return {
                    "error": "OAuth authentication failed",
                    "user": None,
                    "tokens": None,
                }

            # Get or create local user record
            local_user = await self._get_user_by_supabase_id(str(supabase_user.id))
            if not local_user:
                # Create local user if doesn't exist
                local_user = User(
                    supabase_user_id=str(supabase_user.id),
                    email=supabase_user.email,
                    full_name=supabase_user.user_metadata.get("full_name"),
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

            return {
                "error": None,
                "user": UserResponse.model_validate(
                    {**local_user.__dict__, "id": str(local_user.id)}
                ),
                "tokens": tokens,
                "message": "OAuth sign in successful",
            }

        except Exception:
            return {
                "error": "OAuth authentication failed",
                "user": None,
                "tokens": None,
            }

    async def sign_in_with_google_token(
        self, id_token: str, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sign in with Google ID token.

        Args:
            id_token: Google ID token
            redirect_to: Optional redirect URL

        Returns:
            Dict containing user and token information
        """
        try:
            # Authenticate with Supabase using ID token
            supabase_response = supabase_client.sign_in_with_google_token(id_token)

            if supabase_response["error"]:
                return {
                    "error": supabase_response["error"],
                    "user": None,
                    "tokens": None,
                }

            supabase_user = supabase_response["user"]
            if not supabase_user:
                return {
                    "error": "Google authentication failed",
                    "user": None,
                    "tokens": None,
                }

            # Get or create local user record
            local_user = await self._get_user_by_supabase_id(str(supabase_user.id))
            if not local_user:
                # Create local user if doesn't exist
                local_user = User(
                    supabase_user_id=str(supabase_user.id),
                    email=supabase_user.email,
                    full_name=supabase_user.user_metadata.get("full_name"),
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

            return {
                "error": None,
                "user": UserResponse.model_validate(
                    {**local_user.__dict__, "id": str(local_user.id)}
                ),
                "tokens": tokens,
                "message": "Google sign in successful",
            }

        except Exception as e:
            logger.error(f"Google OAuth sign in failed: {e}")
            return {
                "error": "Google authentication failed",
                "user": None,
                "tokens": None,
            }

    async def handle_email_verification(
        self,
        token: str,
        type_param: str,
        email: str,
        redirect_to: Optional[str] = None,
        use_token_hash: bool = False,
    ) -> Dict[str, Any]:
        """
        Handle email verification callback.

        Args:
            token: Email verification token
            type_param: Verification type (signup, recovery, etc.)
            redirect_to: Optional redirect URL

        Returns:
            Dict containing user and token information
        """
        try:
            # Verify the token with Supabase
            supabase_response = await supabase_client.verify_email_token(
                token, type_param, email, use_token_hash
            )

            if supabase_response["error"]:
                return {
                    "error": supabase_response["error"],
                    "user": None,
                    "tokens": None,
                }

            supabase_user = supabase_response["user"]
            supabase_session = supabase_response.get("session")

            if not supabase_user:
                return {
                    "error": "Email verification failed",
                    "user": None,
                    "tokens": None,
                }

            # Get local user record
            local_user = await self._get_user_by_supabase_id(str(supabase_user.id))
            if not local_user:
                return {
                    "error": "User not found in local database",
                    "user": None,
                    "tokens": None,
                }

            # Update user as verified using UPDATE statement
            stmt = update(User).where(User.id == local_user.id).values(is_verified=True)
            await self.db.execute(stmt)
            await self.db.commit()

            # Refresh the user object to get updated data
            await self.db.refresh(local_user)

            # Update last login
            await self._update_last_login(local_user.id)

            # Always create backend tokens for email verification
            tokens = await self._create_tokens(local_user)

            # Create session in local database
            await self._create_session(
                local_user.id, tokens.access_token, tokens.refresh_token
            )

            logger.info(f"Email verification successful: {local_user.email}")

            return {
                "error": None,
                "user": UserResponse.model_validate(
                    {**local_user.__dict__, "id": str(local_user.id)}
                ),
                "tokens": tokens,
                "message": "Email verification successful",
            }

        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return {
                "error": "Email verification failed",
                "user": None,
                "tokens": None,
            }

    async def resend_verification_email(
        self, email: str, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resend email verification link.

        Args:
            email: User's email address
            redirect_to: Optional redirect URL after verification

        Returns:
            Dict containing success or error information
        """
        try:
            # Check if user exists
            local_user = await self._get_user_by_email(email)
            if not local_user:
                return {
                    "error": "User not found",
                    "success": False,
                }

            # Check if user is already verified
            if local_user.is_verified:
                return {
                    "error": "User is already verified",
                    "success": False,
                }

            # Resend verification email via Supabase with redirect to backend
            backend_redirect_url = f"{settings.backend_url}/api/v1/auth/verify"
            supabase_response = await supabase_client.resend_verification_email(
                email, backend_redirect_url
            )

            if supabase_response["error"]:
                return {
                    "error": supabase_response["error"],
                    "success": False,
                }

            logger.info(f"Verification email resent: {email}")

            return {
                "error": None,
                "success": True,
                "message": "Verification email sent successfully",
            }

        except Exception as e:
            logger.error(f"Failed to resend verification email for {email}: {e}")
            return {
                "error": "Failed to resend verification email",
                "success": False,
            }

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
        expires_at = datetime.utcnow() + timedelta(
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
            .values(last_login_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _revoke_session_by_token(self, access_token: str) -> None:
        """Revoke a session by access token."""
        stmt = (
            update(UserSession)
            .where(UserSession.session_token == access_token)
            .values(revoked_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _update_session_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        old_refresh_token: Optional[str] = None,
    ) -> None:
        """Update session tokens."""
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

        stmt = update(UserSession).where(
            UserSession.user_id == user_id, UserSession.revoked_at.is_(None)
        )

        if old_refresh_token:
            stmt = stmt.where(UserSession.refresh_token == old_refresh_token)

        stmt = stmt.values(
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            last_used_at=datetime.utcnow(),
        )
        await self.db.execute(stmt)
        await self.db.commit()
