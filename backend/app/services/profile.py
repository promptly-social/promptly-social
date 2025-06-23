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
import google.auth
import google.auth.transport.requests
import google.oauth2.id_token
import google.oauth2.service_account

from app.core.config import settings
from app.models.profile import SocialConnection, UserPreferences, WritingStyleAnalysis
from app.schemas.profile import SocialConnectionUpdate, UserPreferencesUpdate


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

    async def upsert_user_preferences(
        self, user_id: UUID, preferences_data: UserPreferencesUpdate
    ) -> UserPreferences:
        """Create or update user preferences."""
        try:
            # Check if preferences exist
            existing = await self.get_user_preferences(user_id)

            if existing:
                # Update existing preferences
                update_dict = preferences_data.model_dump()
                update_dict["updated_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated user preferences for {user_id}")
                return existing
            else:
                # Create new preferences
                preferences = UserPreferences(
                    user_id=user_id, **preferences_data.model_dump()
                )
                self.db.add(preferences)
                await self.db.commit()
                await self.db.refresh(preferences)
                logger.info(f"Created user preferences for {user_id}")
                return preferences

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

    # LinkedIn Operations
    def create_linkedin_authorization_url(self, state: str) -> str:
        """Create the LinkedIn authorization URL."""
        if settings.use_unipile_for_linkedin:
            return self._create_unipile_linkedin_auth_url(state)
        else:
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

    def _create_unipile_linkedin_auth_url(self, state: str) -> str:
        """Create Unipile LinkedIn authorization URL using hosted auth wizard."""
        if not settings.unipile_dsn or not settings.unipile_access_token:
            raise ValueError("UNIPILE_DSN and UNIPILE_ACCESS_TOKEN are not configured")

        # Unipile requires generating a hosted auth link via their API
        # We'll use a synchronous approach for URL generation
        import httpx
        import datetime

        redirect_uri = f"{settings.frontend_url}/auth/linkedin/callback"

        # Calculate expiration time (1 hour from now) with exact format required by Unipile
        # Format must match: ^[1-2]\\d{3}-[0-1]\\d-[0-3]\\dT\\d{2}:\\d{2}:\\d{2}.\\d{3}Z$
        expires_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            hours=1
        )
        expires_on = (
            expires_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )  # Truncate to 3 decimal places

        headers = {
            "X-API-KEY": settings.unipile_access_token,
            "Content-Type": "application/json",
        }

        notify_url = f"{settings.backend_url}/api/v1/profile/linkedin/unipile-callback"

        # Warn about localhost URLs in development
        if "localhost" in notify_url or "127.0.0.1" in notify_url:
            logger.warning(
                f"Webhook URL contains localhost ({notify_url}). "
                "Unipile webhooks will not work with localhost URLs. "
                "Consider using ngrok or a public URL for development."
            )

        payload = {
            "type": "create",
            "providers": ["LINKEDIN"],
            "api_url": f"https://{settings.unipile_dsn}",
            "expiresOn": expires_on,
            "success_redirect_url": f"{redirect_uri}?state={state}",
            "failure_redirect_url": f"{settings.frontend_url}/auth/linkedin/error?state={state}",
            "notify_url": notify_url,
            "name": state,  # Use state as the internal ID for matching
        }

        try:
            logger.info(f"Creating Unipile hosted auth link with payload: {payload}")
            with httpx.Client() as client:
                response = client.post(
                    f"https://{settings.unipile_dsn}/api/v1/hosted/accounts/link",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Unipile hosted auth link created successfully: {result}")
                return result["url"]
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Unipile hosted auth API error: {e.response.status_code} - {e.response.text}"
            )
            raise ValueError(f"Failed to create Unipile auth link: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating Unipile hosted auth link: {e}")
            raise ValueError(f"Failed to create Unipile auth link: {str(e)}")

    async def exchange_linkedin_code_for_token(
        self, code: str, user_id: UUID
    ) -> SocialConnection:
        """Exchange authorization code for an access token and fetch user info."""
        if settings.use_unipile_for_linkedin:
            return await self._exchange_unipile_linkedin_code(code, user_id)
        else:
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
            platform_username=user_info.get("name"),
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

    async def _exchange_unipile_linkedin_code(
        self, code: str, user_id: UUID
    ) -> SocialConnection:
        """Exchange Unipile LinkedIn authorization code for account connection."""
        if not settings.unipile_dsn or not settings.unipile_access_token:
            raise ValueError("Unipile DSN or access token is not configured")

        # For Unipile, the "code" is actually an account_id returned from their auth flow
        account_id = code

        # Fetch account details from Unipile
        headers = {
            "Authorization": f"Bearer {settings.unipile_access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Get account information
            response = await client.get(
                f"https://api.unipile.com/api/v1/accounts/{account_id}", headers=headers
            )
            response.raise_for_status()
            account_data = response.json()

        # Extract user information from Unipile account
        platform_username = account_data.get("name", "LinkedIn User")

        # Store all auth data in connection_data JSON field
        connection_data = SocialConnectionUpdate(
            platform_username=platform_username,
            is_active=True,
            connection_data={
                "auth_method": "unipile",
                "account_id": account_id,
                "unipile_account_id": account_id,  # Keep both for backward compatibility
                "provider": account_data.get("provider"),
                "status": account_data.get("status"),
                **account_data,  # Store full account data
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

        # Check auth method - Unipile doesn't need token refresh
        auth_method = (
            connection.connection_data.get("auth_method")
            if connection.connection_data
            else "native"
        )

        if auth_method == "unipile":
            # For Unipile, verify the account is still active
            return await self._verify_unipile_account(connection)
        else:
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

    async def _verify_unipile_account(
        self, connection: SocialConnection
    ) -> Optional[SocialConnection]:
        """Verify Unipile account is still active and update connection data if needed."""
        if not settings.unipile_access_token:
            logger.warning("Unipile access token not configured")
            return connection

        if not connection.connection_data:
            logger.warning("Connection data not found")
            return connection

        account_id = connection.connection_data.get(
            "account_id"
        ) or connection.connection_data.get("unipile_account_id")
        if not account_id:
            logger.warning("Unipile account ID not found in connection data")
            return connection

        try:
            headers = {
                "Authorization": f"Bearer {settings.unipile_access_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.unipile.com/api/v1/accounts/{account_id}",
                    headers=headers,
                )
                response.raise_for_status()
                account_data = response.json()

            # Update connection data if account status changed
            current_status = connection.connection_data.get("status")
            new_status = account_data.get("status")

            if current_status != new_status:
                updated_connection_data = connection.connection_data.copy()
                updated_connection_data.update(account_data)

                connection.connection_data = updated_connection_data
                connection.is_active = new_status == "connected"
                await self.db.commit()
                logger.info(
                    f"Updated Unipile account status from {current_status} to {new_status}"
                )

            return connection

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Account no longer exists
                connection.is_active = False
                await self.db.commit()
                logger.warning(f"Unipile account {account_id} no longer exists")
            else:
                logger.error(f"Error verifying Unipile account: {e}")
            return connection
        except Exception as e:
            logger.error(f"Error verifying Unipile account: {e}")
            return connection

    async def get_unipile_accounts(self) -> List[dict]:
        """Get all connected Unipile accounts."""
        if not settings.unipile_access_token:
            raise ValueError("Unipile access token is not configured")

        headers = {
            "Authorization": f"Bearer {settings.unipile_access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.unipile.com/api/v1/accounts", headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def share_on_linkedin(self, user_id: UUID, text: str) -> dict:
        """Share a text post on LinkedIn for a user."""
        connection = await self.get_social_connection(user_id, "linkedin")
        if not connection or not connection.connection_data:
            raise ValueError("User does not have a valid LinkedIn connection.")

        # Check which auth method was used for this connection
        auth_method = connection.connection_data.get("auth_method", "native")

        if auth_method == "unipile":
            return await self._share_via_unipile(connection, text)
        else:
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

    async def _share_via_unipile(self, connection: SocialConnection, text: str) -> dict:
        """Share a text post on LinkedIn using Unipile API."""
        if not settings.unipile_access_token:
            raise ValueError("Unipile access token is not configured")

        if not connection.connection_data:
            raise ValueError("Connection data not found.")

        account_id = connection.connection_data.get(
            "account_id"
        ) or connection.connection_data.get("unipile_account_id")
        if not account_id:
            raise ValueError("Unipile account ID not found in connection data")

        headers = {
            "Authorization": f"Bearer {settings.unipile_access_token}",
            "Content-Type": "application/json",
        }

        # Using Unipile's messaging API to post to LinkedIn
        payload = {
            "account_id": account_id,
            "text": text,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.unipile.com/api/v1/posts", headers=headers, json=payload
            )
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"Successfully shared post to LinkedIn via Unipile with ID: {result.get('id')}"
            )
            return {"share_id": result.get("id"), "method": "unipile"}

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
        try:
            # Get the Substack connection
            connection = await self.get_social_connection_for_analysis(
                user_id, "substack"
            )

            if not connection:
                logger.warning(f"No Substack connection found for user {user_id}")
                return None

            # if connection.analysis_completed_at:
            #     raise ValueError("Substack analysis has already been completed")

            if not connection.platform_username:
                raise ValueError(
                    "Substack connection has no platform_username configured"
                )

            # Set analysis_started_at timestamp
            connection.analysis_started_at = datetime.now(timezone.utc)
            connection.analysis_completed_at = None  # Reset completed timestamp
            connection.analysis_status = "in_progress"

            await self.db.commit()

            logger.info(f"Started substack analysis for user {user_id}")

            # Trigger async edge function
            await self._trigger_substack_analysis(
                user_id, connection.platform_username, content_to_analyze
            )

            return connection

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error starting substack analysis for {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _trigger_substack_analysis(
        self, user_id: UUID, platform_username: str, content_to_analyze: List[str]
    ) -> None:
        """Trigger the Substack analysis via GCP Cloud Run or Edge Function."""
        try:
            # Prefer Cloud Run if configured
            if settings.gcp_analysis_function_url:
                await self._trigger_gcp_cloud_run(
                    user_id, platform_username, content_to_analyze
                )
            else:
                # Fallback to Supabase Edge Function (if you have one)
                raise NotImplementedError("Edge function trigger not implemented")
        except Exception as e:
            logger.error(f"Error triggering edge function for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _trigger_gcp_cloud_run(
        self, user_id: UUID, platform_username: str, content_to_analyze: List[str]
    ) -> None:
        """Trigger GCP Cloud Run function for analysis."""
        try:
            if not settings.gcp_analysis_function_url:
                logger.error("Missing GCP Cloud Run function URL")
                return

            id_token = None
            auth_req = google.auth.transport.requests.Request()

            if (
                settings.environment == "development"
                and settings.gcp_service_account_key_path
            ):
                # Local development: Use service account key file
                logger.debug("Using service account key for GCP authentication.")
                try:
                    creds = google.oauth2.service_account.IDTokenCredentials.from_service_account_file(
                        settings.gcp_service_account_key_path,
                        target_audience=settings.gcp_analysis_function_url,
                    )
                    creds.refresh(auth_req)
                    id_token = creds.token
                except FileNotFoundError:
                    logger.error(
                        f"Service account key file not found at: {settings.gcp_service_account_key_path}"
                    )
                    raise
            else:
                # Deployed environment: Use default credentials (metadata server)
                logger.debug("Using default credentials for GCP authentication.")
                id_token = google.oauth2.id_token.fetch_id_token(
                    auth_req, settings.gcp_analysis_function_url
                )

            if not id_token:
                logger.error("Could not obtain GCP ID token.")
                return

            headers = {"Authorization": f"Bearer {id_token}"}

            payload = {
                "user_id": str(user_id),
                "platform_username": platform_username,
                "content_to_analyze": content_to_analyze,
            }

            logger.info(
                f"Triggering GCP Cloud Run for user {user_id}. This may take a few minutes..."
            )
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.gcp_analysis_function_url,
                    json=payload,
                    headers=headers,
                    timeout=300.0,  # Increased timeout to 5 minutes
                )
                response.raise_for_status()
            logger.info(f"Successfully triggered GCP Cloud Run for user {user_id}")
        except httpx.ReadTimeout:
            logger.error(
                "Timeout triggering GCP Cloud Run function. The analysis function took too long to respond."
            )
            logger.error(traceback.format_exc())
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error triggering GCP Cloud Run function: {e.response.status_code} - {e.response.text}"
            )
            logger.error(traceback.format_exc())
            raise
        except Exception as e:
            logger.error(f"Error triggering GCP Cloud Run function: {e}")
            logger.error(traceback.format_exc())
            raise

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
