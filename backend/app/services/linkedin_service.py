"""
Service layer for LinkedIn interactions.
"""

from typing import Any, Dict, List, Optional

import httpx
from app.core.config import settings
from app.models.profile import SocialConnection
from loguru import logger


class LinkedInService:
    """Service for interacting with the LinkedIn API,
    including helper methods for obtaining and refreshing native OAuth tokens."""

    BASE_API_URL = "https://api.linkedin.com/v2"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    USER_ME_URL = "https://api.linkedin.com/v2/me"

    # Analytics-specific scopes
    ANALYTICS_SCOPES = "r_member_postAnalytics r_member_profileAnalytics"

    # ------------------------
    # Static helper utilities
    # ------------------------
    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access & refresh tokens (native flow)."""
        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            raise ValueError("LinkedIn client ID or secret not configured")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                LinkedInService.TOKEN_URL, data=payload, headers=headers
            )
            response.raise_for_status()
            token_data = response.json()

        return token_data

    @staticmethod
    async def exchange_code_for_analytics_token(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for analytics access & refresh tokens."""
        if not settings.linkedin_analytics_client_id or not settings.linkedin_analytics_client_secret:
            raise ValueError("LinkedIn analytics client ID or secret not configured")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.linkedin_analytics_client_id,
            "client_secret": settings.linkedin_analytics_client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                LinkedInService.TOKEN_URL, data=payload, headers=headers
            )
            response.raise_for_status()
            token_data = response.json()

        return token_data

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired LinkedIn access token."""
        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            raise ValueError("LinkedIn client ID or secret not configured")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LinkedInService.TOKEN_URL, data=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def refresh_analytics_access_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired LinkedIn analytics access token."""
        if not settings.linkedin_analytics_client_id or not settings.linkedin_analytics_client_secret:
            raise ValueError("LinkedIn analytics client ID or secret not configured")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.linkedin_analytics_client_id,
            "client_secret": settings.linkedin_analytics_client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LinkedInService.TOKEN_URL, data=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """Fetch user information from LinkedIn's userinfo endpoint."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(LinkedInService.USERINFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_user_profile(access_token: str) -> Dict[str, Any]:
        """Fetch user profile from LinkedIn's me endpoint."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(LinkedInService.USER_ME_URL, headers=headers)
            response.raise_for_status()
            return response.json()

    def __init__(self, connection: SocialConnection):
        """
        Initialize the LinkedInService.

        :param connection: The social connection object with LinkedIn credentials.
        """
        if connection.platform != "linkedin":
            raise ValueError("SocialConnection is not for LinkedIn.")
        if not connection.connection_data:
            raise ValueError("No connection data found for LinkedIn.")

        self.connection = connection
        self.access_token = connection.connection_data.get("access_token")
        self.linkedin_user_id = connection.connection_data.get("linkedin_user_id")

        if not self.access_token or not self.linkedin_user_id:
            raise ValueError("Missing access token or user ID for LinkedIn.")

    def _get_headers(self) -> Dict[str, str]:
        """Get the required headers for LinkedIn API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def _register_upload(self, media_type: str) -> Dict[str, Any]:
        """
        Register an image or video to be uploaded to LinkedIn.

        :param media_type: The type of media to upload ("image" or "video").
        :return: The response from LinkedIn containing the upload URL and asset URN.
        """
        endpoint = f"{self.BASE_API_URL}/assets?action=registerUpload"
        recipe = (
            "urn:li:digitalmediaRecipe:feedshare-image"
            if media_type == "image"
            else "urn:li:digitalmediaRecipe:feedshare-video"
        )
        payload = {
            "registerUploadRequest": {
                "recipes": [recipe],
                "owner": f"urn:li:person:{self.linkedin_user_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    endpoint, json=payload, headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error registering LinkedIn upload: {e.response.text}")
                raise

    async def _upload_media_content(self, upload_url: str, media_content: bytes):
        """
        Uploads media content (bytes) to the provided LinkedIn upload URL.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    upload_url,
                    content=media_content,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Error uploading media content to LinkedIn: {e.response.text}"
                )
                raise

    async def upload_media(self, media_content: bytes, media_type: str) -> str:
        """
        Registers and uploads a media file from memory to LinkedIn.

        :param media_content: The content of the media file in bytes.
        :param media_type: The type of media ("image" or "video").
        :return: The LinkedIn asset URN for the uploaded media.
        """
        registration = await self._register_upload(media_type)
        upload_url = registration["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn = registration["value"]["asset"]

        await self._upload_media_content(upload_url, media_content)

        return asset_urn

    async def share_post(
        self,
        text: str,
        article_url: Optional[str] = None,
        media_items: Optional[List[Dict[str, Any]]] = None,
        visibility: str = "PUBLIC",
    ):
        """
        Share a post to LinkedIn with optional media.

        :param text: The content of the post.
        :param article_url: Optional URL to share as an article.
        :param media_items: A list of media items to share (images/videos with their URNs).
        :param visibility: The visibility of the post ("PUBLIC" or "CONNECTIONS").
        """
        endpoint = f"{self.BASE_API_URL}/ugcPosts"
        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "NONE",
        }

        logger.info(
            f"LinkedIn share_post called with: text_length={len(text)}, article_url={article_url}, media_items_count={len(media_items) if media_items else 0}"
        )

        # Handle different media scenarios
        if article_url and (not media_items or len(media_items) == 0):
            # Article only
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [{"status": "READY", "originalUrl": article_url}]
        elif media_items and len(media_items) > 0:
            # Media items (images/videos)
            first_media = media_items[0]
            if "media" in first_media:
                media_urn = first_media["media"]
                if "image" in media_urn.lower():
                    share_content["shareMediaCategory"] = "IMAGE"
                elif "video" in media_urn.lower():
                    share_content["shareMediaCategory"] = "VIDEO"
                else:
                    # Default to image if we can't determine
                    share_content["shareMediaCategory"] = "IMAGE"

            share_content["media"] = [
                {"status": "READY", **item} for item in media_items
            ]

            # If there's also an article URL with media, we prioritize media
            # LinkedIn doesn't support both article and media in the same post
        # If neither article_url nor media_items, keep shareMediaCategory as "NONE"

        post_data = {
            "author": f"urn:li:person:{self.linkedin_user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        logger.info(f"LinkedIn API payload: {post_data}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    endpoint, json=post_data, headers=self._get_headers()
                )
                response.raise_for_status()
                logger.info(
                    f"Successfully shared post to LinkedIn for user {self.connection.user_id}"
                )
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error sharing post to LinkedIn: {e.response.text}")
                logger.error(f"Failed payload was: {post_data}")
                raise
