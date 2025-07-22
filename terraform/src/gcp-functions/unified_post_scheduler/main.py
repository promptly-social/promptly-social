import json
import logging
import os
from datetime import datetime, timezone
import asyncio
from typing import Dict, Any, List, Optional
import traceback
from uuid import UUID

import functions_framework
import httpx
import sys
from google.cloud import storage

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.cloud_sql_client import get_cloud_sql_client, CloudSQLClient


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts UUID objects to strings."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


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


def get_cloud_sql_db():
    """Initialize Cloud SQL client."""
    return get_cloud_sql_client()


async def _process_scheduled_posts_async(request):
    """
    Async implementation of process_scheduled_posts.
    """
    headers = {"Access-Control-Allow-Origin": "*"}
    db_client = None

    try:
        logger.info("Starting unified post scheduler execution")
        start_time = datetime.now(timezone.utc)

        # Initialize Cloud SQL client
        db_client = get_cloud_sql_db()

        # Get posts scheduled for publishing
        posts_to_publish = await retry_with_exponential_backoff(
            get_posts_to_publish, db_client
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
        results = await process_posts_batch(db_client, posts_to_publish)

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
                },
                cls=UUIDEncoder,
            ),
            200,
            headers,
        )

    except Exception as e:
        logger.error(f"Error in unified post scheduler: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return (
            json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
            headers,
        )
    finally:
        # Ensure Cloud SQL client is properly closed to prevent event loop issues
        if db_client:
            try:
                logger.info("Closing Cloud SQL client")
                await db_client.close_async()
            except Exception as cleanup_error:
                logger.warning(f"Error closing Cloud SQL client: {cleanup_error}")

        # Also close the global client if it exists
        try:
            from shared.cloud_sql_client import close_cloud_sql_client_async

            await close_cloud_sql_client_async()
        except Exception as global_cleanup_error:
            logger.warning(
                f"Error closing global Cloud SQL client: {global_cleanup_error}"
            )


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

    # Use asyncio.run() in a safe way for Cloud Functions
    try:
        # Check if there's already an event loop running
        try:
            asyncio.get_running_loop()
            # If we get here, there's already a loop running
            # We need to run in a new thread with proper cleanup
            import concurrent.futures

            def run_in_thread():
                # Create a new event loop in this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        _process_scheduled_posts_async(request)
                    )
                finally:
                    # Ensure all tasks are completed before closing
                    try:
                        # Cancel any remaining tasks
                        pending = asyncio.all_tasks(new_loop)
                        if pending:
                            logger.info(f"Cancelling {len(pending)} pending tasks")
                            for task in pending:
                                task.cancel()
                            # Wait for tasks to be cancelled
                            new_loop.run_until_complete(
                                asyncio.gather(*pending, return_exceptions=True)
                            )
                    except Exception as cleanup_error:
                        logger.warning(f"Error during task cleanup: {cleanup_error}")
                    finally:
                        new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(_process_scheduled_posts_async(request))

    except Exception as e:
        logger.error(f"Error in process_scheduled_posts wrapper: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return (
            json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
            {"Access-Control-Allow-Origin": "*"},
        )


async def get_posts_to_publish(client: CloudSQLClient) -> List[Dict[str, Any]]:
    """
    Query database for posts scheduled in the last 10 minutes that haven't been published.
    """
    try:
        now = datetime.now(timezone.utc)

        logger.info(f"Querying for posts scheduled before {now}")

        # Query for scheduled posts in the time window
        query = """
            SELECT * FROM posts 
            WHERE status = :status 
            AND posted_at IS NULL 
            AND scheduled_at <= :now 
            ORDER BY scheduled_at ASC
        """

        posts = await client.execute_query_async(
            query,
            {"status": "scheduled", "now": now},
        )

        logger.info(f"Found {len(posts)} posts ready for publishing")

        return posts

    except Exception as e:
        logger.error(f"Error querying posts to publish: {e}")
        raise


async def process_posts_batch(
    client: CloudSQLClient, posts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a batch of posts for publishing with error handling.
    """
    results = []

    for post in posts:
        try:
            logger.info(f"Processing post {post['id']} for user {post['user_id']}")
            result = await process_single_post(client, post)
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
                    client,
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


async def process_single_post(
    client: CloudSQLClient, post: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a single post for publishing.
    """
    post_id = post["id"]
    user_id = post["user_id"]

    try:
        # Get LinkedIn connection for the user
        linkedin_connection = await get_linkedin_connection(client, user_id)
        if not linkedin_connection:
            raise Exception("LinkedIn connection not found")

        # Refresh token if needed
        refreshed_connection = await refresh_token_if_needed(
            client, linkedin_connection
        )
        if not refreshed_connection:
            raise Exception("Failed to refresh LinkedIn token")

        # Get post media
        media_items = await get_post_media(client, post_id)

        # Share to LinkedIn
        share_result = await share_to_linkedin(client, post, refreshed_connection, media_items)
        if not share_result:
            raise Exception("Failed to share to LinkedIn")

        # Update post status to posted
        await update_post_status(
            client,
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
    client: CloudSQLClient, user_id: str
) -> Optional[Dict[str, Any]]:
    """Get user's LinkedIn connection data."""
    try:
        query = """
            SELECT * FROM social_connections 
            WHERE user_id = :user_id 
            AND platform = :platform
        """

        results = await client.execute_query_async(
            query, {"user_id": user_id, "platform": "linkedin"}
        )

        if not results:
            logger.error(f"LinkedIn connection not found for user {user_id}")
            return None

        connection = results[0]
        connection_data = connection.get("connection_data", {})

        if not connection_data.get("access_token"):
            logger.error(f"No access token found for user {user_id}")
            return None

        return connection

    except Exception as e:
        logger.error(f"Error retrieving LinkedIn connection: {e}")
        return None


async def refresh_token_if_needed(
    client: CloudSQLClient, connection: Dict[str, Any]
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
            update_query = """
                UPDATE social_connections 
                SET connection_data = :connection_data
                WHERE id = :connection_id
            """

            await client.execute_update_async(
                update_query,
                {
                    "connection_data": updated_connection_data,
                    "connection_id": connection["id"],
                },
            )

            # Update the connection object
            connection["connection_data"] = updated_connection_data

            logger.info("Successfully refreshed LinkedIn access token")
            return connection

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None


async def get_post_media(client: CloudSQLClient, post_id: str) -> list:
    """Get media attachments for a post."""
    try:
        query = """
            SELECT * FROM post_media
            WHERE post_id = :post_id
        """

        results = await client.execute_query_async(query, {"post_id": post_id})

        return results or []
    except Exception as e:
        logger.error(f"Error retrieving post media: {e}")
        return []


async def upload_media_to_linkedin(
    access_token: str, linkedin_user_id: str, media_content: bytes, media_type: str
) -> str:
    """
    Upload media to LinkedIn and return the asset URN.

    :param access_token: LinkedIn access token
    :param linkedin_user_id: LinkedIn user ID
    :param media_content: Media content as bytes
    :param media_type: Type of media ("image" or "video")
    :return: LinkedIn asset URN
    """
    try:
        # Step 1: Register upload
        register_endpoint = "https://api.linkedin.com/v2/assets?action=registerUpload"
        recipe = (
            "urn:li:digitalmediaRecipe:feedshare-image"
            if media_type == "image"
            else "urn:li:digitalmediaRecipe:feedshare-video"
        )

        register_payload = {
            "registerUploadRequest": {
                "recipes": [recipe],
                "owner": f"urn:li:person:{linkedin_user_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        async with httpx.AsyncClient() as client:
            # Register upload
            response = await client.post(
                register_endpoint, json=register_payload, headers=headers
            )
            response.raise_for_status()
            registration = response.json()

            # Extract upload URL and asset URN
            upload_url = registration["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            asset_urn = registration["value"]["asset"]

            # Step 2: Upload media content
            upload_response = await client.post(
                upload_url,
                content=media_content,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            upload_response.raise_for_status()

            logger.info(f"Successfully uploaded {media_type} to LinkedIn: {asset_urn}")
            return asset_urn

    except Exception as e:
        logger.error(f"Error uploading media to LinkedIn: {e}")
        raise


async def download_media_from_gcs(storage_path: str) -> bytes:
    """Download media content from Google Cloud Storage."""
    try:
        # Initialize GCS client
        gcs_client = storage.Client()
        bucket_name = os.getenv("GCS_BUCKET_NAME", "promptly-social-scribe-media")
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(storage_path)

        # Download media content
        media_content = blob.download_as_bytes()
        logger.info(f"Downloaded media from GCS: {storage_path}")
        return media_content

    except Exception as e:
        logger.error(f"Error downloading media from GCS {storage_path}: {e}")
        raise


async def update_media_linkedin_urn(
    client: CloudSQLClient, media_id: str, linkedin_asset_urn: str
) -> bool:
    """Update the LinkedIn asset URN for a media item."""
    try:
        query = """
            UPDATE post_media
            SET linkedin_asset_urn = :linkedin_asset_urn
            WHERE id = :media_id
        """

        rows_affected = await client.execute_update_async(
            query, {"linkedin_asset_urn": linkedin_asset_urn, "media_id": media_id}
        )

        if rows_affected > 0:
            logger.info(f"Updated media {media_id} with LinkedIn asset URN")
            return True
        else:
            logger.error(f"Failed to update media {media_id}")
            return False

    except Exception as e:
        logger.error(f"Error updating media LinkedIn URN: {e}")
        return False


async def share_to_linkedin(
    client: CloudSQLClient, post_data: Dict[str, Any], connection: Dict[str, Any], media_items: list = None
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
                # Check if we already have a LinkedIn asset URN
                if media.get("linkedin_asset_urn"):
                    media_payloads.append({"media": media["linkedin_asset_urn"]})
                # If not, upload the media to LinkedIn first
                elif media.get("storage_path") and media.get("media_type"):
                    try:
                        logger.info(f"Uploading media to LinkedIn: {media['storage_path']}")

                        # Download media from GCS
                        media_content = await download_media_from_gcs(media["storage_path"])

                        # Upload to LinkedIn
                        asset_urn = await upload_media_to_linkedin(
                            access_token, linkedin_user_id, media_content, media["media_type"]
                        )

                        # Store the asset URN in the database for future use
                        await update_media_linkedin_urn(client, media["id"], asset_urn)

                        media_payloads.append({"media": asset_urn})

                    except Exception as e:
                        logger.error(f"Failed to upload media {media['id']}: {e}")
                        # Continue without this media item
                        continue

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
                "shared_at": datetime.now(timezone.utc),
                "response": result,
            }

    except Exception as e:
        logger.error(f"Error sharing to LinkedIn: {e}")
        return None


async def update_post_status(
    client: CloudSQLClient, post_id: str, updates: Dict[str, Any]
) -> bool:
    """Update post status and sharing information."""
    try:
        # Build dynamic update query based on provided fields
        set_clauses = []
        params = {"post_id": post_id}

        for key, value in updates.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

        query = f"""
            UPDATE posts 
            SET {", ".join(set_clauses)}
            WHERE id = :post_id
        """

        rows_affected = await client.execute_update_async(query, params)

        if rows_affected > 0:
            logger.info(f"Updated post {post_id} with status: {updates.get('status')}")
            return True
        else:
            logger.error(f"Failed to update post {post_id}")
            return False

    except Exception as e:
        logger.error(f"Error updating post status: {e}")
        return False
