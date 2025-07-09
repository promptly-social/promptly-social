"""
Content service for handling content-related business logic.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
import urllib.parse
import traceback
import httpx
from loguru import logger
from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.profile import SocialConnection, UserPreferences, WritingStyleAnalysis
from app.models.content_strategies import ContentStrategy
from app.schemas.profile import SocialConnectionUpdate, UserPreferencesUpdate

from app.utils.gcp import trigger_gcp_cloud_run


class ProfileService:
    """Service class for profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # User Preferences Operations
    async def get_user_preferences(self, user_id: UUID) -> Optional[UserPreferences]:
        """Get user preferences."""
        try:
            query = select(UserPreferences).where(UserPreferences.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user preferences for {user_id}: {e}")
            raise

    async def get_content_strategies(self, user_id: UUID) -> List[ContentStrategy]:
        """Get content strategies for a user."""
        try:
            query = select(ContentStrategy).where(ContentStrategy.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting content strategies for {user_id}: {e}")
            raise

    async def upsert_content_strategy(
        self, user_id: UUID, platform: str, strategy: str
    ) -> ContentStrategy:
        """Create or update a content strategy for a platform."""
        try:
            # Check if strategy exists
            query = select(ContentStrategy).where(
                and_(
                    ContentStrategy.user_id == user_id,
                    ContentStrategy.platform == platform,
                )
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing strategy
                existing.strategy = strategy
                existing.updated_at = datetime.now(timezone.utc)
                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated content strategy {platform} for {user_id}")
                return existing
            else:
                # Create new strategy
                strategy_obj = ContentStrategy(
                    user_id=user_id,
                    platform=platform,
                    strategy=strategy,
                )
                self.db.add(strategy_obj)
                await self.db.commit()
                await self.db.refresh(strategy_obj)
                logger.info(f"Created content strategy {platform} for {user_id}")
                return strategy_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error upserting content strategy {platform} for {user_id}: {e}"
            )
            raise

    async def create_default_linkedin_strategy(self, user_id: UUID) -> ContentStrategy:
        """Create default LinkedIn content strategy for a user."""
        default_linkedin_strategy = """Best Practices for Crafting Engaging LinkedIn Post Text

Start with a Strong Hook: Begin the post with a compelling question, a surprising statistic, or a bold statement to immediately capture the reader's attention and stop them from scrolling.

Encourage Conversation: End your post with a clear call-to-action or an open-ended question that prompts readers to share their own experiences, opinions, or advice in the comments. Frame the text to start a discussion, not just to broadcast information.

Write for Readability: Use short paragraphs, single-sentence lines, and bullet points to break up large blocks of text. This makes the post easier to scan and digest on a mobile device.

Provide Genuine Value: The core of the text should offer insights, tips, or a personal story that is valuable to your target audience. Avoid pure self-promotion and focus on sharing expertise or relatable experiences.

Incorporate Strategic Mentions: When mentioning other people or companies, tag them using @. Limit this to a maximum of five relevant tags per post to encourage a response without appearing spammy.

Use Niche Hashtags: Integrate up to three specific and relevant hashtags at the end of your post. These should act as keywords for your topic (e.g., #ProjectManagementTips instead of just #Management) to connect with interested communities."""

        return await self.upsert_content_strategy(
            user_id, "linkedin", default_linkedin_strategy
        )

    async def upsert_user_preferences(
        self, user_id: UUID, preferences_data: UserPreferencesUpdate
    ) -> UserPreferences:
        """Create or update user preferences."""
        try:
            # Handle content strategies separately
            content_strategies_data = preferences_data.content_strategies
            preferences_data_dict = preferences_data.model_dump(exclude_unset=True)
            preferences_data_dict.pop(
                "content_strategies", None
            )  # Remove content_strategies from preferences data

            # Check if preferences exist
            existing = await self.get_user_preferences(user_id)

            if existing:
                # Update existing preferences
                update_dict = preferences_data_dict
                update_dict["updated_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated user preferences for {user_id}")
            else:
                # Create new preferences
                preferences = UserPreferences(user_id=user_id, **preferences_data_dict)
                self.db.add(preferences)
                await self.db.commit()
                await self.db.refresh(preferences)
                existing = preferences
                logger.info(f"Created user preferences for {user_id}")

            # Handle content strategies if provided
            if content_strategies_data:
                for platform, strategy in content_strategies_data.items():
                    await self.upsert_content_strategy(user_id, platform, strategy)

            # Ensure default LinkedIn strategy exists
            existing_strategies = await self.get_content_strategies(user_id)
            linkedin_strategy_exists = any(
                s.platform == "linkedin" for s in existing_strategies
            )
            if not linkedin_strategy_exists:
                await self.create_default_linkedin_strategy(user_id)

            return existing

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error upserting user preferences for {user_id}: {e}")
            raise

    # Social Connections Operations
    async def get_social_connections(self, user_id: UUID) -> List[SocialConnection]:
        """Get all social connections for a user."""
        try:
            query = select(SocialConnection).where(SocialConnection.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting social connections for {user_id}: {e}")
            raise

    async def get_social_connection(
        self, user_id: UUID, platform: str
    ) -> Optional[SocialConnection]:
        """Get a specific social connection."""
        try:
            query = select(SocialConnection).where(
                and_(
                    SocialConnection.user_id == user_id,
                    SocialConnection.platform == platform,
                    SocialConnection.is_active,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting social connection {platform} for {user_id}: {e}"
            )
            raise

    async def get_social_connection_for_analysis(
        self, user_id: UUID, platform: str
    ) -> Optional[SocialConnection]:
        """Get a specific social connection for analysis (doesn't filter by is_active)."""
        try:
            query = select(SocialConnection).where(
                and_(
                    SocialConnection.user_id == user_id,
                    SocialConnection.platform == platform,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting social connection {platform} for analysis for {user_id}: {e}"
            )
            raise

    async def upsert_social_connection(
        self, user_id: UUID, platform: str, connection_data: SocialConnectionUpdate
    ) -> SocialConnection:
        """Create or update a social connection."""
        try:
            # Check if connection exists
            existing = await self.get_social_connection_for_analysis(user_id, platform)

            # Handle disconnect case
            if connection_data.is_active is False and existing:
                return await self._disconnect_social_connection(
                    user_id, platform, existing
                )

            if existing:
                # Update existing connection
                update_dict = connection_data.model_dump(exclude_unset=True)
                update_dict["updated_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated social connection {platform} for {user_id}")
                return existing
            else:
                # Create new connection
                connection = SocialConnection(
                    user_id=user_id,
                    platform=platform,
                    **connection_data.model_dump(exclude_unset=True),
                )
                self.db.add(connection)
                await self.db.commit()
                await self.db.refresh(connection)
                logger.info(f"Created social connection {platform} for {user_id}")
                return connection

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error upserting social connection {platform} for {user_id}: {e}"
            )
            raise

    async def _disconnect_social_connection(
        self, user_id: UUID, platform: str, connection: SocialConnection
    ) -> SocialConnection:
        """Handle disconnection of a social connection."""
        try:
            # Clear connection data and set inactive
            connection.is_active = False
            connection.connection_data = None
            connection.platform_username = None
            connection.updated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(connection)
            logger.info(f"Disconnected social connection {platform} for {user_id}")
            return connection

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error disconnecting social connection {platform} for {user_id}: {e}"
            )
            raise

    # LinkedIn Operations
    def create_linkedin_authorization_url(self, state: str) -> str:
        """Create the LinkedIn authorization URL."""
        return self._create_native_linkedin_auth_url(state)

    def _create_native_linkedin_auth_url(self, state: str) -> str:
        """Create the native LinkedIn authorization URL."""
        if not settings.linkedin_client_id:
            raise ValueError("LINKEDIN_CLIENT_ID is not configured")

        redirect_uri = f"{settings.frontend_url}/auth/linkedin/callback"

        params = {
            "response_type": "code",
            "client_id": settings.linkedin_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid profile email w_member_social",  # Using OIDC scopes + sharing
        }
        auth_url = (
            "https://www.linkedin.com/oauth/v2/authorization?"
            + urllib.parse.urlencode(params)
        )
        return auth_url

    async def exchange_linkedin_code_for_token(
        self, code: str, user_id: UUID
    ) -> SocialConnection:
        """Exchange authorization code for an access token and fetch user info."""
        return await self._exchange_native_linkedin_code(code, user_id)

    async def _exchange_native_linkedin_code(
        self, code: str, user_id: UUID
    ) -> SocialConnection:
        """Exchange native LinkedIn authorization code for an access token and fetch user info."""
        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            raise ValueError("LinkedIn client ID or secret is not configured")

        redirect_uri = f"{settings.frontend_url}/auth/linkedin/callback"
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=payload, headers=headers)
            response.raise_for_status()
            token_data = response.json()

        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data["expires_in"]
        scope = token_data["scope"]

        user_info = await self._get_linkedin_user_info(access_token)

        # Store all auth data in connection_data JSON field
        connection_data = SocialConnectionUpdate(
            is_active=True,
            connection_data={
                "auth_method": "native",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                ).isoformat(),
                "scope": scope,
                "linkedin_user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "picture": user_info.get("picture"),
            },
        )

        return await self.upsert_social_connection(user_id, "linkedin", connection_data)

    async def _get_linkedin_user_info(self, access_token: str) -> dict:
        """Fetch user information from LinkedIn's userinfo endpoint."""
        user_info_url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def refresh_linkedin_token(self, user_id: UUID) -> Optional[SocialConnection]:
        """Refresh an expired LinkedIn access token."""
        connection = await self.get_social_connection(user_id, "linkedin")
        if not connection:
            return None

        return await self._refresh_native_linkedin_token(connection, user_id)

    async def _refresh_native_linkedin_token(
        self, connection: SocialConnection, user_id: UUID
    ) -> Optional[SocialConnection]:
        """Refresh native LinkedIn access token."""
        if not connection.connection_data:
            return None

        connection_data = connection.connection_data
        refresh_token = connection_data.get("refresh_token")

        if not refresh_token:
            return None

        # Check if token is expiring soon (e.g., within the next 5 minutes)
        expires_at_str = connection_data.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(
                    expires_at_str.replace("Z", "+00:00")
                )
                if expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
                    return connection  # Token is still valid
            except (ValueError, TypeError):
                # If we can't parse the date, proceed with refresh
                pass

        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            raise ValueError("LinkedIn client ID or secret is not configured")

        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=payload)
            response.raise_for_status()
            token_data = response.json()

        # Update connection_data with new tokens
        updated_connection_data = connection_data.copy()
        updated_connection_data.update(
            {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get(
                    "refresh_token", refresh_token
                ),  # LinkedIn might not always return a new refresh token
                "expires_at": (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=token_data["expires_in"])
                ).isoformat(),
                "scope": token_data.get("scope", connection_data.get("scope")),
            }
        )

        update_data = SocialConnectionUpdate(connection_data=updated_connection_data)
        return await self.upsert_social_connection(user_id, "linkedin", update_data)

    async def share_on_linkedin(self, user_id: UUID, text: str) -> dict:
        """Share a text post on LinkedIn for a user."""
        connection = await self.get_social_connection(user_id, "linkedin")
        if not connection or not connection.connection_data:
            raise ValueError("User does not have a valid LinkedIn connection.")

        return await self._share_via_native_linkedin(connection, text, user_id)

    async def _share_via_native_linkedin(
        self, connection: SocialConnection, text: str, user_id: UUID
    ) -> dict:
        """Share a text post on LinkedIn using native LinkedIn API."""
        # First try to refresh the token if needed
        refreshed_connection = await self.refresh_linkedin_token(user_id)
        if refreshed_connection:
            connection = refreshed_connection

        if not connection.connection_data:
            raise ValueError("Connection data not found.")

        connection_data = connection.connection_data
        access_token = connection_data.get("access_token")
        if not access_token:
            raise ValueError("Access token not found in connection data.")

        # The author URN is stored in connection_data during auth
        author_urn = connection_data.get("linkedin_user_id")
        if not author_urn:
            # Fallback to fetching it again if not present
            user_info = await self._get_linkedin_user_info(access_token)
            author_urn = user_info.get("sub")
            if not author_urn:
                raise ValueError("Could not determine LinkedIn user URN.")
            # Update the connection_data with the author URN
            updated_connection_data = connection_data.copy()
            updated_connection_data["linkedin_user_id"] = author_urn
            connection.connection_data = updated_connection_data
            await self.db.commit()

        share_url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        payload = {
            "author": f"urn:li:person:{author_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(share_url, headers=headers, json=payload)
            response.raise_for_status()

            share_id = response.headers.get("x-restli-id")
            logger.info(f"Successfully shared post to LinkedIn with ID: {share_id}")
            return {"share_id": share_id, "method": "native"}

    async def analyze_substack(
        self, user_id: UUID, content_to_analyze: List[str]
    ) -> Optional[SocialConnection]:
        """
        Analyze Substack content for a user.

        This method:
        1. Sets analysis_started_at timestamp
        2. Triggers async edge function for analysis
        3. Edge function will set analysis_completed_at when done

        Args:
            user_id: UUID of the user to analyze

        Returns:
            Updated SocialConnection with analysis_started_at set
        """
        return await self._analyze_platform(user_id, "substack", content_to_analyze)

    async def analyze_linkedin(
        self, user_id: UUID, content_to_analyze: List[str]
    ) -> Optional[SocialConnection]:
        """
        Analyze LinkedIn content for a user.

        This method:
        1. Sets analysis_started_at timestamp
        2. Triggers async edge function for analysis
        3. Edge function will set analysis_completed_at when done

        Args:
            user_id: UUID of the user to analyze

        Returns:
            Updated SocialConnection with analysis_started_at set
        """
        return await self._analyze_platform(user_id, "linkedin", content_to_analyze)

    async def analyze_import_sample(
        self, user_id: UUID, text_sample: str, content_to_analyze: List[str]
    ) -> None:
        """
        Analyze imported text sample for a user.

        This method directly calls the GCP Cloud Function for import analysis
        without needing a social connection.

        Args:
            user_id: UUID of the user to analyze
            text_sample: The text sample to analyze
            content_to_analyze: List of content types to analyze
        """
        try:
            logger.info(f"Starting import sample analysis for user {user_id}")

            # Trigger the cloud function for import analysis
            await self._trigger_import_analysis(
                user_id, text_sample, content_to_analyze
            )

        except Exception as e:
            logger.error(f"Error starting import sample analysis for {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _analyze_platform(
        self, user_id: UUID, platform: str, content_to_analyze: List[str]
    ) -> Optional[SocialConnection]:
        """
        Generic method to analyze content for any supported platform.

        Args:
            user_id: UUID of the user to analyze
            platform: Platform to analyze (substack, linkedin)
            content_to_analyze: List of content types to analyze

        Returns:
            Updated SocialConnection with analysis_started_at set
        """
        try:
            # Get the platform connection
            connection = await self.get_social_connection_for_analysis(
                user_id, platform
            )

            if not connection:
                logger.warning(f"No {platform} connection found for user {user_id}")
                return None

            # Validate connection has required data
            if platform == "substack" and not connection.platform_username:
                raise ValueError(
                    f"{platform} connection has no platform_username configured"
                )
            elif platform == "linkedin":
                # For LinkedIn, we need the account_id from connection_data
                if not connection.connection_data or not connection.connection_data.get(
                    "account_id"
                ):
                    raise ValueError(
                        f"{platform} connection has no account_id configured"
                    )

            # Set analysis_started_at timestamp
            connection.analysis_started_at = datetime.now(timezone.utc)
            connection.analysis_completed_at = None  # Reset completed timestamp
            connection.analysis_status = "in_progress"

            await self.db.commit()

            logger.info(f"Started {platform} analysis for user {user_id}")

            # Trigger async edge function
            await self._trigger_platform_analysis(
                user_id, platform, connection, content_to_analyze
            )

            return connection

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error starting {platform} analysis for {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _trigger_platform_analysis(
        self,
        user_id: UUID,
        platform: str,
        connection: SocialConnection,
        content_to_analyze: List[str],
    ) -> None:
        """Trigger the platform analysis via GCP Cloud Run or Edge Function."""
        try:
            # Prefer Cloud Run if configured
            if settings.gcp_analysis_function_url:
                await self._trigger_gcp_cloud_run(
                    user_id, platform, connection, content_to_analyze
                )
            else:
                # Fallback to Supabase Edge Function (if you have one)
                raise NotImplementedError("Edge function trigger not implemented")
        except Exception as e:
            logger.error(f"Error triggering edge function for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _trigger_gcp_cloud_run(
        self,
        user_id: UUID,
        platform: str,
        connection: SocialConnection,
        content_to_analyze: List[str],
    ) -> None:
        """Trigger GCP Cloud Run function for analysis."""
        if not settings.gcp_analysis_function_url:
            logger.error("Missing GCP Cloud Run function URL")
            return

        # Get the platform identifier based on platform type
        if platform == "substack":
            platform_identifier = connection.platform_username
        elif platform == "linkedin":
            platform_identifier = (
                connection.connection_data.get("account_id")
                if connection.connection_data
                else None
            )
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        if not platform_identifier:
            raise ValueError(f"Missing platform identifier for {platform}")

        payload = {
            "user_id": str(user_id),
            "platform": platform,
            "platform_username": platform_identifier,
            "content_to_analyze": content_to_analyze,
        }

        await trigger_gcp_cloud_run(
            target_url=settings.gcp_analysis_function_url,
            payload=payload,
            timeout=300.0,
        )

    async def _trigger_import_analysis(
        self,
        user_id: UUID,
        text_sample: str,
        content_to_analyze: List[str],
    ) -> None:
        """Trigger GCP Cloud Run function for import sample analysis."""
        if not settings.gcp_analysis_function_url:
            logger.error("Missing GCP Cloud Run function URL")
            return

        payload = {
            "user_id": str(user_id),
            "platform": "import",
            "platform_username": "import_sample",  # Placeholder value
            "content_to_analyze": content_to_analyze,
            "text_sample": text_sample,
        }

        await trigger_gcp_cloud_run(
            target_url=settings.gcp_analysis_function_url,
            payload=payload,
            timeout=60.0,  # Import analysis should be faster
        )

    # Writing Style Analysis Operations
    async def get_writing_style_analysis(
        self, user_id: UUID, source: str
    ) -> Optional[WritingStyleAnalysis]:
        """Get writing style analysis for a specific source (import, substack, linkedin)."""
        try:
            query = select(WritingStyleAnalysis).where(
                and_(
                    WritingStyleAnalysis.user_id == user_id,
                    WritingStyleAnalysis.source == source,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting writing style analysis {source} for {user_id}: {e}"
            )
            raise

    async def upsert_writing_style_analysis(
        self, user_id: UUID, source: str, analysis_data: str
    ) -> WritingStyleAnalysis:
        """Create or update writing style analysis for a specific source."""
        try:
            # Check if analysis exists
            existing = await self.get_writing_style_analysis(user_id, source)

            if existing:
                # Update existing analysis
                update_dict = {"analysis_data": analysis_data}
                update_dict["updated_at"] = datetime.now(timezone.utc)
                if (
                    "last_analyzed_at" not in update_dict
                    or update_dict["last_analyzed_at"] is None
                ):
                    update_dict["last_analyzed_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated writing style analysis {source} for {user_id}")
                return existing
            else:
                analysis = WritingStyleAnalysis(
                    user_id=user_id,
                    source=source,
                    analysis_data=analysis_data,
                )
                self.db.add(analysis)
                await self.db.commit()
                await self.db.refresh(analysis)
                logger.info(f"Created writing style analysis {source} for {user_id}")
                return analysis

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error upserting writing style analysis {source} for {user_id}: {e}"
            )
            raise

    # ------------------------------------------------------------------
    # Consolidated Operations
    # ------------------------------------------------------------------

    async def get_latest_writing_style_analysis(
        self, user_id: UUID
    ) -> Optional[WritingStyleAnalysis]:
        """Return the most recently analyzed writing style record for a user, irrespective of source."""
        try:
            query = (
                select(WritingStyleAnalysis)
                .where(WritingStyleAnalysis.user_id == user_id)
                .order_by(
                    desc(WritingStyleAnalysis.last_analyzed_at),
                    desc(WritingStyleAnalysis.updated_at),
                )
                .limit(1)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting latest writing style analysis for {user_id}: {e}"
            )
            raise
