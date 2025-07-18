import json
import logging
import os
from datetime import datetime, timezone
import asyncio
from typing import Dict, Any, List
import traceback

import functions_framework
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
from cloud_sql_client import get_cloud_sql_client
from substack_analyzer import SubstackAnalyzer
from linkedin_analyzer import LinkedInAnalyzer
from import_sample_analyzer import ImportSampleAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cloud_sql_db():
    """Initialize Cloud SQL client."""
    return get_cloud_sql_client()


def fetch_content(
    platform: str,
    platform_identifier: str,
    current_bio: str,
    content_to_analyze: List[str],
    text_sample: str = None,
) -> Dict[str, Any]:
    """
    Fetch and analyze content using the appropriate analyzer based on platform.
    """
    logger.info(
        f"Starting comprehensive analysis for {platform_identifier} on {platform}"
    )

    # Get configuration from environment
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    if platform == "substack":
        max_posts = int(os.getenv("MAX_POSTS_TO_ANALYZE", "10"))
        analyzer = SubstackAnalyzer(
            max_posts=max_posts, openrouter_api_key=openrouter_api_key
        )
        return analyzer.analyze_substack(
            platform_identifier, current_bio, content_to_analyze
        )

    elif platform == "linkedin":
        max_posts = int(os.getenv("MAX_POSTS_TO_ANALYZE_LINKEDIN", "20"))
        analyzer = LinkedInAnalyzer(
            max_posts=max_posts,
            openrouter_api_key=openrouter_api_key,
        )
        return analyzer.analyze_linkedin(
            platform_identifier, current_bio, content_to_analyze
        )

    elif platform == "import":
        if not text_sample:
            raise ValueError("text_sample is required for import platform analysis")

        analyzer = ImportSampleAnalyzer(openrouter_api_key=openrouter_api_key)
        return analyzer.analyze_import_sample(
            text_sample, current_bio, content_to_analyze
        )

    else:
        raise ValueError(f"Unsupported platform: {platform}")


async def update_analysis_results(
    db_client,
    user_id: str,
    analysis_result: Dict[str, Any],
    platform: str,
) -> None:
    """Update the social connection with analysis results."""
    try:
        # Store websites, substacks, topics, and bio
        websites = analysis_result.get("websites", [])
        substacks = analysis_result.get("substacks", [])
        topics = analysis_result.get("topics", [])
        bio = analysis_result.get("bio", "")

        if websites or substacks or topics or bio:
            # Fetch existing user preferences
            existing_prefs = db_client.execute_query(
                "SELECT * FROM user_preferences WHERE user_id = :user_id",
                {"user_id": user_id},
            )

            if existing_prefs:
                # Update existing preferences
                pref = existing_prefs[0]
                existing_websites = pref.get("websites", []) or []
                existing_substacks = pref.get("substacks", []) or []
                existing_topics = pref.get("topics_of_interest", []) or []

                updated_websites = list(set(existing_websites + websites))
                updated_substacks = list(set(existing_substacks + substacks))
                updated_topics = list(set(existing_topics + topics))

                update_query = """
                    UPDATE user_preferences 
                    SET websites = :websites, 
                        substacks = :substacks, 
                        topics_of_interest = :topics,
                        bio = COALESCE(:bio, bio),
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """

                db_client.execute_update(
                    update_query,
                    {
                        "user_id": user_id,
                        "websites": updated_websites,
                        "substacks": updated_substacks,
                        "topics": updated_topics,
                        "bio": bio if bio else None,
                    },
                )
            else:
                # Create new preferences
                insert_query = """
                    INSERT INTO user_preferences (user_id, websites, substacks, topics_of_interest, bio)
                    VALUES (:user_id, :websites, :substacks, :topics, :bio)
                """

                db_client.execute_update(
                    insert_query,
                    {
                        "user_id": user_id,
                        "websites": websites,
                        "substacks": substacks,
                        "topics": topics,
                        "bio": bio,
                    },
                )

            logger.info(f"Updated user preferences for user {user_id}")

        if analysis_result.get("writing_style"):
            # Store writing style analysis
            upsert_query = """
                INSERT INTO writing_style_analysis 
                (user_id, platform, analysis_data, content_count, last_analyzed_at)
                VALUES (:user_id, :platform, :analysis_data, :content_count, NOW())
                ON CONFLICT (user_id, platform) 
                DO UPDATE SET 
                    analysis_data = EXCLUDED.analysis_data,
                    content_count = EXCLUDED.content_count,
                    last_analyzed_at = NOW(),
                    updated_at = NOW()
            """

            db_client.execute_update(
                upsert_query,
                {
                    "user_id": user_id,
                    "platform": platform,
                    "analysis_data": analysis_result["writing_style"],
                    "content_count": len(analysis_result.get("content_analyzed", [])),
                },
            )

            logger.info(f"Updated writing style analysis for user {user_id}")

        # Update social connection with results and completion timestamp (only for platforms that use connections)
        if platform != "import":
            update_connection_query = """
                UPDATE social_connections 
                SET analysis_completed_at = NOW(),
                    analysis_status = 'completed',
                    updated_at = NOW()
                WHERE user_id = :user_id AND platform = :platform
            """

            rows_affected = db_client.execute_update(
                update_connection_query, {"user_id": user_id, "platform": platform}
            )

            if rows_affected > 0:
                logger.info(f"Updated social connection for user {user_id}")
            else:
                logger.error(f"Failed to update social connection for user {user_id}")
        else:
            logger.info("Skipped social connection update for import platform")

    except Exception as e:
        logger.error(f"Error updating analysis results: {e}")
        raise


async def mark_analysis_failed(
    db_client,
    user_id: str,
    error_message: str,
    connection_data: Dict[str, Any],
    platform: str = "substack",
) -> None:
    """Mark analysis as failed."""
    try:
        updated_connection_data = {
            **connection_data,
            "analysis_error": error_message,
            "analysis_failed_at": datetime.now(timezone.utc).isoformat(),
            "analysis_status": "error",
        }

        update_query = """
            UPDATE social_connections 
            SET connection_data = :connection_data,
                analysis_started_at = NULL,
                analysis_completed_at = NULL,
                analysis_status = 'error',
                updated_at = NOW()
            WHERE user_id = :user_id AND platform = :platform
        """

        db_client.execute_update(
            update_query,
            {
                "user_id": user_id,
                "platform": platform,
                "connection_data": json.dumps(updated_connection_data),
            },
        )

        logger.info(f"Marked analysis as failed for user {user_id}")

    except Exception as e:
        logger.error(f"Error marking analysis as failed: {e}")


@functions_framework.http
def analyze(request):
    """
    GCP Cloud Function for analyzing social media content (Substack and LinkedIn).

    Expected request body:
    {
        "user_id": "uuid",
        "platform": "substack" | "linkedin" | "import",
        "platform_username": "username" (for Substack) or "account_id" (for LinkedIn),
        "content_to_analyze": ["bio", "interests", "substacks", "writing_style"]
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
        platform = request_json.get(
            "platform", "substack"
        )  # Default to substack for backward compatibility
        platform_username = request_json.get("platform_username")
        content_to_analyze = request_json.get("content_to_analyze", [])
        text_sample = request_json.get("text_sample")  # For import platform

        # Validation based on platform
        if platform == "import":
            if not user_id or not text_sample or not content_to_analyze:
                return (
                    json.dumps(
                        {
                            "success": False,
                            "error": "user_id, text_sample and content_to_analyze are required for import platform",
                        }
                    ),
                    400,
                    headers,
                )
        else:
            if not user_id or not platform_username or not content_to_analyze:
                return (
                    json.dumps(
                        {
                            "success": False,
                            "error": "user_id, platform_username and content_to_analyze are required",
                        }
                    ),
                    400,
                    headers,
                )

        if platform == "import":
            logger.info(
                f"Starting {platform} analysis for user {user_id} with text sample"
            )
        else:
            logger.info(
                f"Starting {platform} analysis for user {user_id} with identifier {platform_username}"
            )

        # Initialize Cloud SQL client
        db_client = get_cloud_sql_db()

        # For import platform, we don't need to check social connections
        connection = None
        if platform != "import":
            # Verify the social connection exists and is being analyzed
            connections = db_client.execute_query(
                "SELECT * FROM social_connections WHERE user_id = :user_id AND platform = :platform",
                {"user_id": user_id, "platform": platform},
            )

            if not connections:
                error_msg = f"{platform} connection not found for user {user_id}"
                logger.error(error_msg)
                return (
                    json.dumps({"success": False, "error": error_msg}),
                    404,
                    headers,
                )

            connection = connections[0]

            if not connection.get("analysis_started_at"):
                error_msg = f"Analysis not started for user {user_id}"
                logger.error(error_msg)
                return (
                    json.dumps({"success": False, "error": error_msg}),
                    400,
                    headers,
                )

        # Get current user bio
        user_preferences = db_client.execute_query(
            "SELECT bio FROM user_preferences WHERE user_id = :user_id",
            {"user_id": user_id},
        )

        current_bio = ""
        if user_preferences:
            current_bio = user_preferences[0].get("bio", "") or ""

        # Perform the analysis
        try:
            analysis_result = fetch_content(
                platform,
                platform_username,
                current_bio,
                content_to_analyze,
                text_sample,
            )

            # Update database with results
            asyncio.run(
                update_analysis_results(
                    db_client,
                    user_id,
                    analysis_result,
                    platform,
                )
            )

            logger.info(
                f"Successfully completed {platform} analysis for user {user_id}"
            )

            return (
                json.dumps(
                    {
                        "success": True,
                        "message": "Analysis completed successfully",
                        "content_to_analyze": content_to_analyze,
                        "analysis_summary": {
                            "topics_count": len(analysis_result.get("topics", [])),
                            "websites_count": len(analysis_result.get("websites", [])),
                            "substacks_count": len(
                                analysis_result.get("substacks", [])
                            ),
                            "bio": len(analysis_result.get("bio", "")),
                            "writing_style": analysis_result.get("writing_style", ""),
                        },
                    }
                ),
                200,
                headers,
            )

        except Exception as analysis_error:
            logger.error(f"Error during analysis: {analysis_error}")

            # Mark analysis as failed (only for platforms with social connections)
            if platform != "import":
                asyncio.run(
                    mark_analysis_failed(
                        db_client,
                        user_id,
                        str(analysis_error),
                        connection.get("connection_data", {}),
                        platform,
                    )
                )
            else:
                logger.error(
                    f"Import analysis failed for user {user_id}: {analysis_error}"
                )

            return (
                json.dumps(
                    {
                        "success": False,
                        "error": f"Analysis failed: {str(analysis_error)}",
                    }
                ),
                500,
                headers,
            )

    except Exception as e:
        logger.error(f"Error in analyze_substack function: {e}")
        logger.error(traceback.format_exc())
        return (json.dumps({"success": False, "error": str(e)}), 500, headers)
