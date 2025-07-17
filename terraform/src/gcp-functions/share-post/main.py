import json
import logging
import os
from datetime import datetime, timezone
import asyncio
from typing import Dict, Any, Optional
import traceback

import functions_framework
import httpx
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for retry logic
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
INITIAL_RETRY_DELAY = 1  # seconds


async def retry_with_exponential_backoff(func, *args, **kwargs):
    """Retry function with exponential backoff."""
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            result = await func(*args, **kwargs)
            if result is not None:
                return result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == MAX_RETRY_ATTEMPTS - 1:
                logger.error(f"All {MAX_RETRY_ATTEMPTS} attempts failed")
                raise

            # Exponential backoff
            delay = INITIAL_RETRY_DELAY * (2**attempt)
            logger.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)

    return None


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_service_key:
        raise ValueError("Missing Supabase configuration")

    return create_client(supabase_url, supabase_service_key)


async def get_post_data(
    supabase: Client, user_id: str, post_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve post data from database."""
    try:
        response = (
            supabase.table("posts")
            .select("*")
            .eq("id", post_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            logger.error(f"Post {post_id} not found for user {user_id}")
            return None

        post = response.data[0]

        # Validate post is scheduled
        if post.get("status") != "scheduled":
            logger.error(
                f"Post {post_id} is not in scheduled status: {post.get('status')}"
            )
            return None

        return post

    except Exception as e:
        logger.error(f"Error retrieving post data: {e}")
        return None


async def get_linkedin_connection(
    supabase: Client, user_id: str
) -> Optional[Dict[str, Any]]:
    """Get user's LinkedIn connection data."""
    try:
        response = (
            supabase.table("social_connections")
            .select("*")
            .eq("user_id", user_id)
            .eq("platform", "linkedin")
            .execute()
        )

        if not response.data:
            logger.error(f"LinkedIn connection not found for user {user_id}")
            return None

        connection = response.data[0]
        connection_data = connection.get("connection_data", {})

        if not connection_data.get("access_token"):
            logger.error(f"No access token found for user {user_id}")
            return None

        return connection

    except Exception as e:
        logger.error(f"Error retrieving LinkedIn connection: {e}")
        return None


async def refresh_token_if_needed(
    supabase: Client, connection: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Refresh LinkedIn access token if needed."""
    try:
        connection_data = connection.get("connection_data", {})
        # access_token = connection_data.get("access_token")
        refresh_token = connection_data.get("refresh_token")
        expires_at = connection_data.get("expires_at")

        if not refresh_token:
            logger.error("No refresh token available")
            return None

        # Check if token needs refresh (refresh if expires within 1 hour)
        threshold_minutes = int(os.getenv("LINKEDIN_TOKEN_REFRESH_THRESHOLD", "60"))

        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(
                    expires_at.replace("Z", "+00:00")
                )
                time_until_expiry = expires_datetime - datetime.now(timezone.utc)

                if time_until_expiry.total_seconds() > (threshold_minutes * 60):
                    logger.info("Token is still valid, no refresh needed")
                    return connection
            except Exception as e:
                logger.warning(
                    f"Error parsing expires_at: {e}, proceeding with refresh"
                )

        # Refresh the token
        logger.info("Refreshing LinkedIn access token")

        linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
        linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")

        if not linkedin_client_id or not linkedin_client_secret:
            logger.error("LinkedIn client credentials not configured")
            return None

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": linkedin_client_id,
            "client_secret": linkedin_client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data=payload,
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )
                return None

            token_data = response.json()

            # Update connection data with new tokens
            new_expires_at = datetime.now(timezone.utc).timestamp() + token_data.get(
                "expires_in", 3600
            )
            new_expires_at_iso = datetime.fromtimestamp(
                new_expires_at, timezone.utc
            ).isoformat()

            updated_connection_data = {
                **connection_data,
                "access_token": token_data.get("access_token"),
                "expires_at": new_expires_at_iso,
            }

            # Update refresh token if provided
            if token_data.get("refresh_token"):
                updated_connection_data["refresh_token"] = token_data.get(
                    "refresh_token"
                )

            # Update database
            supabase.table("social_connections").update(
                {"connection_data": updated_connection_data}
            ).eq("id", connection["id"]).execute()

            # Update the connection object
            connection["connection_data"] = updated_connection_data

            logger.info("Successfully refreshed LinkedIn access token")
            return connection

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None


async def get_post_media(supabase: Client, post_id: str) -> list:
    """Get media attachments for a post."""
    try:
        response = (
            supabase.table("post_media").select("*").eq("post_id", post_id).execute()
        )

        return response.data or []
    except Exception as e:
        logger.error(f"Error retrieving post media: {e}")
        return []


async def share_to_linkedin(
    post_data: Dict[str, Any], connection: Dict[str, Any], media_items: list = None
) -> Optional[Dict[str, Any]]:
    """Share post to LinkedIn using the API."""
    try:
        connection_data = connection.get("connection_data", {})
        access_token = connection_data.get("access_token")
        linkedin_user_id = connection_data.get("linkedin_user_id")

        if not access_token or not linkedin_user_id:
            logger.error("Missing LinkedIn credentials")
            return None

        # Prepare post content
        text = post_data.get("content", "")
        article_url = post_data.get("article_url")

        # Build share content - match the logic from linkedin_service.py
        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "NONE",
        }

        # Convert media items to the format expected by LinkedIn service logic
        media_payloads = []
        if media_items:
            for media in media_items:
                if media.get("linkedin_asset_urn"):
                    media_payloads.append({"media": media["linkedin_asset_urn"]})

        # Handle different media scenarios - match linkedin_service.py logic
        if article_url and (not media_payloads or len(media_payloads) == 0):
            # Article only
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [{"status": "READY", "originalUrl": article_url}]
        elif media_payloads and len(media_payloads) > 0:
            # Media items (images/videos)
            first_media = media_payloads[0]
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
                {"status": "READY", **item} for item in media_payloads
            ]

            # If there's also an article URL with media, we prioritize media
            # LinkedIn doesn't support both article and media in the same post
        # If neither article_url nor media_payloads, keep shareMediaCategory as "NONE"

        # Build post data
        post_payload = {
            "author": f"urn:li:person:{linkedin_user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        # Make API call to LinkedIn
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                json=post_payload,
                headers=headers,
            )

            if response.status_code not in [200, 201]:
                logger.error(
                    f"LinkedIn API error: {response.status_code} - {response.text}"
                )
                return None

            result = response.json()
            logger.info(f"Successfully shared post to LinkedIn: {result.get('id')}")

            return {
                "linkedin_post_id": result.get("id"),
                "shared_at": datetime.now(timezone.utc).isoformat(),
                "response": result,
            }

    except Exception as e:
        logger.error(f"Error sharing to LinkedIn: {e}")
        return None


async def update_post_status(
    supabase: Client, post_id: str, updates: Dict[str, Any]
) -> bool:
    """Update post status and sharing information."""
    try:
        response = supabase.table("posts").update(updates).eq("id", post_id).execute()

        if response.data:
            logger.info(f"Updated post {post_id} with status: {updates.get('status')}")
            return True
        else:
            logger.error(f"Failed to update post {post_id}")
            return False

    except Exception as e:
        logger.error(f"Error updating post status: {e}")
        return False


@functions_framework.http
def share_post(request):
    """
    GCP Cloud Function for sharing posts to LinkedIn.

    Expected request body:
    {
        "user_id": "uuid",
        "post_id": "uuid"
    }
    """
    # Handle CORS
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    headers = {"Access-Control-Allow-Origin": "*"}

    try:
        # Parse request
        request_json = request.get_json(silent=True)

        if not request_json:
            return (
                json.dumps({"success": False, "error": "Invalid JSON"}),
                400,
                headers,
            )

        user_id = request_json.get("user_id")
        post_id = request_json.get("post_id")

        if not user_id or not post_id:
            return (
                json.dumps(
                    {
                        "success": False,
                        "error": "user_id and post_id are required",
                    }
                ),
                400,
                headers,
            )

        logger.info(f"Starting post sharing for user {user_id}, post {post_id}")

        # Initialize Supabase client
        supabase = get_supabase_client()

        # Get post data with retry
        post_data = asyncio.run(
            retry_with_exponential_backoff(get_post_data, supabase, user_id, post_id)
        )
        if not post_data:
            return (
                json.dumps(
                    {"success": False, "error": "Post not found or not scheduled"}
                ),
                404,
                headers,
            )

        # Get LinkedIn connection with retry
        linkedin_connection = asyncio.run(
            retry_with_exponential_backoff(get_linkedin_connection, supabase, user_id)
        )
        if not linkedin_connection:
            return (
                json.dumps(
                    {"success": False, "error": "LinkedIn connection not found"}
                ),
                404,
                headers,
            )

        # Refresh token if needed (no retry for token refresh to avoid infinite loops)
        refreshed_connection = asyncio.run(
            refresh_token_if_needed(supabase, linkedin_connection)
        )
        if not refreshed_connection:
            # Update post with authentication error
            asyncio.run(
                update_post_status(
                    supabase,
                    post_id,
                    {
                        "status": "failed",
                        "sharing_error": "LinkedIn authentication failed - token refresh failed",
                    },
                )
            )
            return (
                json.dumps(
                    {"success": False, "error": "Failed to refresh LinkedIn token"}
                ),
                401,
                headers,
            )

        # Get post media with retry
        media_items = asyncio.run(
            retry_with_exponential_backoff(get_post_media, supabase, post_id)
        )

        # Share to LinkedIn with single retry for transient errors
        share_result = None
        try:
            share_result = asyncio.run(
                share_to_linkedin(post_data, refreshed_connection, media_items)
            )
            if not share_result:
                # Try once more for transient LinkedIn API issues
                logger.info("Retrying LinkedIn share after initial failure")
                asyncio.sleep(2)
                share_result = asyncio.run(
                    share_to_linkedin(post_data, refreshed_connection, media_items)
                )
        except Exception as e:
            logger.error(f"LinkedIn sharing failed: {e}")

        if not share_result:
            # Update post with error
            asyncio.run(
                update_post_status(
                    supabase,
                    post_id,
                    {
                        "status": "scheduled",
                        "sharing_error": "Failed to share to LinkedIn after retries",
                    },
                )
            )
            return (
                json.dumps({"success": False, "error": "Failed to share to LinkedIn"}),
                500,
                headers,
            )

        # Update post status to posted with retry
        update_success = asyncio.run(
            retry_with_exponential_backoff(
                update_post_status,
                supabase,
                post_id,
                {
                    "status": "posted",
                    "posted_at": share_result["shared_at"],
                    "linkedin_post_id": share_result["linkedin_post_id"],
                    "sharing_error": None,
                },
            )
        )

        if not update_success:
            logger.warning(
                f"Failed to update post status for {post_id}, but sharing was successful"
            )

        logger.info(f"Successfully shared post {post_id} to LinkedIn")

        return (
            json.dumps(
                {
                    "success": True,
                    "message": "Post shared successfully",
                    "linkedin_post_id": share_result["linkedin_post_id"],
                    "shared_at": share_result["shared_at"],
                }
            ),
            200,
            headers,
        )

    except Exception as e:
        logger.error(f"Error in share_post function: {e}")
        logger.error(traceback.format_exc())
        return (json.dumps({"success": False, "error": str(e)}), 500, headers)
