import json
import logging
import os
from datetime import datetime, timezone, timedelta
import asyncio
from typing import Dict, Any, List, Optional
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


@functions_framework.http
def process_scheduled_posts(request):
    """
    Process all posts scheduled for publishing in the last 5 minutes.

    This function is triggered by Cloud Scheduler every 5 minutes.
    No request payload required.
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
        logger.info("Starting unified post scheduler execution")
        start_time = datetime.now(timezone.utc)

        # Initialize Supabase client
        supabase = get_supabase_client()

        # Get posts scheduled for publishing
        posts_to_publish = asyncio.run(
            retry_with_exponential_backoff(get_posts_to_publish, supabase)
        )

        if not posts_to_publish:
            logger.info("No posts found for publishing")
            return (
                json.dumps(
                    {
                        "success": True,
                        "message": "No posts to publish",
                        "posts_processed": 0,
                        "execution_time_seconds": (
                            datetime.now(timezone.utc) - start_time
                        ).total_seconds(),
                    }
                ),
                200,
                headers,
            )

        logger.info(f"Found {len(posts_to_publish)} posts to publish")

        # Process each post
        results = asyncio.run(process_posts_batch(supabase, posts_to_publish))

        # Calculate summary statistics
        successful_posts = sum(1 for r in results if r["success"])
        failed_posts = len(results) - successful_posts
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        logger.info(
            f"Completed processing: {successful_posts} successful, {failed_posts} failed, "
            f"{execution_time:.2f}s execution time"
        )

        return (
            json.dumps(
                {
                    "success": True,
                    "message": "Post processing completed",
                    "posts_processed": len(posts_to_publish),
                    "successful_posts": successful_posts,
                    "failed_posts": failed_posts,
                    "execution_time_seconds": execution_time,
                    "results": results,
                }
            ),
            200,
            headers,
        )

    except Exception as e:
        logger.error(f"Error in unified post scheduler: {e}")
        logger.error(traceback.format_exc())
        return (
            json.dumps({"success": False, "error": str(e), "posts_processed": 0}),
            500,
            headers,
        )


async def get_posts_to_publish(supabase: Client) -> List[Dict[str, Any]]:
    """
    Query database for posts scheduled in the last 10 minutes that haven't been published.
    """
    try:
        # Calculate time window: 10 minutes ago to now
        now = datetime.now(timezone.utc)
        ten_minutes_ago = now - timedelta(minutes=10)

        logger.info(f"Querying for posts scheduled between {ten_minutes_ago} and {now}")

        # Query for scheduled posts in the time window
        response = (
            supabase.table("posts")
            .select("*")
            .eq("status", "scheduled")
            .is_("posted_at", "null")
            .gte("scheduled_at", ten_minutes_ago.isoformat())
            .lte("scheduled_at", now.isoformat())
            .order("scheduled_at", desc=False)
            .execute()
        )

        posts = response.data or []
        logger.info(f"Found {len(posts)} posts ready for publishing")

        return posts

    except Exception as e:
        logger.error(f"Error querying posts to publish: {e}")
        raise


async def process_posts_batch(
    supabase: Client, posts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a batch of posts for publishing with error handling.
    """
    results = []

    for post in posts:
        try:
            logger.info(f"Processing post {post['id']} for user {post['user_id']}")
            result = await process_single_post(supabase, post)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process post {post['id']}: {e}")
            results.append(
                {
                    "post_id": post["id"],
                    "user_id": post["user_id"],
                    "success": False,
                    "error": str(e),
                }
            )

            # Update post with error status
            try:
                await update_post_status(
                    supabase,
                    post["id"],
                    {
                        "sharing_error": f"Unified scheduler error: {str(e)}",
                        "status": "scheduled",  # Keep as scheduled for retry
                    },
                )
            except Exception as update_error:
                logger.error(
                    f"Failed to update error status for post {post['id']}: {update_error}"
                )

    return results


async def process_single_post(supabase: Client, post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single post for publishing.
    """
    post_id = post["id"]
    user_id = post["user_id"]

    try:
        # Get LinkedIn connection for the user
        linkedin_connection = await get_linkedin_connection(supabase, user_id)
        if not linkedin_connection:
            raise Exception("LinkedIn connection not found")

        # Refresh token if needed
        refreshed_connection = await refresh_token_if_needed(
            supabase, linkedin_connection
        )
        if not refreshed_connection:
            raise Exception("Failed to refresh LinkedIn token")

        # Get post media
        media_items = await get_post_media(supabase, post_id)

        # Share to LinkedIn
        share_result = await share_to_linkedin(post, refreshed_connection, media_items)
        if not share_result:
            raise Exception("Failed to share to LinkedIn")

        # Update post status to posted
        await update_post_status(
            supabase,
            post_id,
            {
                "status": "posted",
                "posted_at": share_result["shared_at"],
                "linkedin_post_id": share_result["linkedin_post_id"],
                "sharing_error": None,
            },
        )

        logger.info(f"Successfully published post {post_id}")

        return {
            "post_id": post_id,
            "user_id": user_id,
            "success": True,
            "linkedin_post_id": share_result["linkedin_post_id"],
            "shared_at": share_result["shared_at"],
        }

    except Exception as e:
        logger.error(f"Error processing post {post_id}: {e}")
        raise


# Import helper functions from existing share-post function
# These functions are copied and adapted from the existing share-post/main.py


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
