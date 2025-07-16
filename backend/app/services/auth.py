"""
Authentication service containing business logic for user management.
Integrates Supabase auth with local database operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from loguru import logger
import uuid
from urllib.parse import urlencode, quote_plus
from app.services.linkedin_service import LinkedInService

from app.models.user import User, UserSession
from app.models.idea_bank import IdeaBank
from app.models.posts import Post
from app.models.profile import SocialConnection, UserPreferences, WritingStyleAnalysis
from app.models.content_strategies import ContentStrategy
from app.models.daily_suggestion_schedule import DailySuggestionSchedule
from app.models.chat import Conversation
from app.schemas.auth import (
    TokenResponse,
    UserResponse,
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

    # ------------------------------
    # Native (3-legged) LinkedIn flow for w_member_social scope
    # ------------------------------
    async def initiate_linkedin_native(
        self, redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate LinkedIn authorization URL with extended scopes."""
        try:
            if not settings.linkedin_client_id:
                return {"error": "LinkedIn client ID not configured", "url": None}

            state = uuid.uuid4().hex
            redirect_uri = redirect_to or f"{settings.frontend_url}/auth/callback"

            params = {
                "response_type": "code",
                "client_id": settings.linkedin_client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": "openid profile email w_member_social",
            }
            query = urlencode(params, quote_via=quote_plus)
            auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{query}"

            logger.info("Generated LinkedIn authorization URL")
            return {"error": None, "url": auth_url, "state": state}
        except Exception as e:
            logger.error(f"LinkedIn OAuth sign in failed: {e}")
            return {"error": "Native OAuth sign in failed", "url": None}

    async def handle_linkedin_callback(
        self, code: str, state: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Handle LinkedIn OAuth callback for native 3-legged flow.
        Exchanges code for token, gets user info, creates/updates user and social connection,
        and creates a local session.
        """
        try:
            # 1. Exchange authorization code for token
            token_data = await LinkedInService.exchange_code_for_token(
                code, redirect_uri
            )
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            scope = token_data.get("scope")

            # 2. Get user info from LinkedIn
            user_info = await LinkedInService.get_user_info(access_token)
            email = user_info.get("email")
            linkedin_user_id = user_info.get("sub")
            full_name = user_info.get("name")
            avatar_url = user_info.get("picture")

            if not email:
                raise Exception("Email not returned from LinkedIn")

            # 3. Get or create local user record
            local_user = await self._get_user_by_email(email)
            if not local_user:
                local_user = User(
                    email=email,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    is_verified=True,  # Trusting LinkedIn email
                )
                self.db.add(local_user)
                await self.db.commit()
                await self.db.refresh(local_user)
            else:
                # Update user info with latest from LinkedIn
                local_user.full_name = full_name
                local_user.avatar_url = avatar_url
                local_user.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                await self.db.refresh(local_user)

            # 4. Create or update SocialConnection
            stmt = select(SocialConnection).where(
                SocialConnection.user_id == local_user.id,
                SocialConnection.platform == "linkedin",
            )
            result = await self.db.execute(stmt)
            connection = result.scalar_one_or_none()

            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                if expires_in
                else None
            )

            connection_data = {
                "auth_method": "oauth2",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "scope": scope,
                "linkedin_user_id": linkedin_user_id,
                "email": email,
                "full_name": full_name,
                "avatar_url": avatar_url,
            }

            if connection:
                connection.connection_data = connection_data
                connection.is_active = True
                connection.updated_at = datetime.now(timezone.utc)
            else:
                connection = SocialConnection(
                    user_id=local_user.id,
                    platform="linkedin",
                    connection_data=connection_data,
                    is_active=True,
                )
                self.db.add(connection)

            await self._update_last_login(local_user.id)
            await self.db.commit()

            # 5. Create backend tokens and session
            tokens = await self._create_tokens(local_user)
            await self._create_session(
                local_user.id, tokens.access_token, tokens.refresh_token
            )

            logger.info(f"User signed in successfully with LinkedIn: {email}")

            user_response = UserResponse.model_validate(
                {**local_user.__dict__, "id": str(local_user.id)}
            )

            return {
                "error": None,
                "user": user_response,
                "tokens": tokens,
                "message": "Sign in successful",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"LinkedIn OAuth callback failed: {e}")
            return {"error": "OAuth callback failed", "user": None, "tokens": None}

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

    # All email/password related methods have been removed.
    # The file continues with private helper methods.

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
