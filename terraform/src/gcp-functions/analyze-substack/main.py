import json
import logging
import os
from datetime import datetime, timezone
import asyncio
from typing import Dict, Any, List
import traceback

import functions_framework
from supabase import create_client, Client
from substack_analyzer import SubstackAnalyzer
from linkedin_analyzer import LinkedInAnalyzer
from import_sample_analyzer import ImportSampleAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_service_key:
        raise ValueError("Missing Supabase configuration")

    return create_client(supabase_url, supabase_service_key)


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
        unipile_access_token = os.getenv("UNIPILE_ACCESS_TOKEN")
        unipile_dsn = os.getenv("UNIPILE_DSN")
        analyzer = LinkedInAnalyzer(
            max_posts=max_posts,
            openrouter_api_key=openrouter_api_key,
            unipile_access_token=unipile_access_token,
            unipile_dsn=unipile_dsn,
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
    supabase: Client,
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
            # Fetch user preferences without .single() to avoid error when no records exist
            user_preferences_result = (
                supabase.table("user_preferences")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            # Create a mock object to maintain the same interface
            user_preferences = type(
                "obj",
                (object,),
                {
                    "data": user_preferences_result.data[0]
                    if user_preferences_result.data
                    else None
                },
            )()

            if user_preferences.data:
                existing_websites = user_preferences.data.get("websites", [])
                user_preferences.data["websites"] = list(
                    set(existing_websites + websites)
                )

                existing_substacks = user_preferences.data.get("substacks", [])
                user_preferences.data["substacks"] = list(
                    set(existing_substacks + substacks)
                )

                existing_topics = user_preferences.data.get("topics_of_interest", [])
                user_preferences.data["topics_of_interest"] = list(
                    set(existing_topics + topics)
                )

                user_preferences.data["bio"] = (
                    user_preferences.data["bio"] or bio
                )  # keep the existing bio if it exists

                preferences_response = (
                    supabase.table("user_preferences")
                    .update(user_preferences.data)
                    .eq("user_id", user_id)
                    .execute()
                )

            else:
                preferences_response = (
                    supabase.table("user_preferences")
                    .insert(
                        {
                            "user_id": user_id,
                            "websites": websites,
                            "substacks": substacks,
                            "topics_of_interest": topics,
                            "bio": bio,
                        }
                    )
                    .execute()
                )

            if preferences_response.data:
                logger.info(f"Created user preferences for user {user_id}")
            else:
                logger.error(f"Failed to create user preferences for user {user_id}")

        # Store writing style analysis
        writing_style_data = {
            "user_id": user_id,
            "source": platform,  # Use the actual platform (substack, linkedin, or import)
            "analysis_data": analysis_result["writing_style"],
            "last_analyzed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Upsert writing style analysis using the unique constraint on (user_id)
        style_response = (
            supabase.table("writing_style_analysis")
            .upsert(writing_style_data, on_conflict="user_id")
            .execute()
        )

        # Update social connection with results and completion timestamp (only for platforms that use connections)
        if platform != "import":
            response = (
                supabase.table("social_connections")
                .update(
                    {
                        "analysis_completed_at": datetime.now(timezone.utc).isoformat(),
                        "analysis_status": "completed",
                    }
                )
                .eq("user_id", user_id)
                .eq("platform", platform)
                .execute()
            )

            if response.data:
                logger.info(f"Updated social connection for user {user_id}")
            else:
                logger.error(f"Failed to update social connection for user {user_id}")
        else:
            logger.info("Skipped social connection update for import platform")

        if style_response.data:
            logger.info(f"Updated writing style analysis for user {user_id}")
        else:
            logger.warning(
                f"Failed to update writing style analysis for user {user_id}"
            )

    except Exception as e:
        logger.error(f"Error updating analysis results: {e}")
        raise


async def mark_analysis_failed(
    supabase: Client,
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

        supabase.table("social_connections").update(
            {
                "connection_data": updated_connection_data,
                "analysis_started_at": None,
                "analysis_completed_at": None,
                "analysis_status": "error",
            }
        ).eq("user_id", user_id).eq("platform", platform).execute()

        logger.info(f"Marked analysis as failed for user {user_id}")

    except Exception as e:
        logger.error(f"Error marking analysis as failed: {e}")


@functions_framework.http
def analyze_substack(request):
    """
    GCP Cloud Function for analyzing social media content (Substack and LinkedIn).

    Expected request body:
    {
        "user_id": "uuid",
        "platform": "substack" | "linkedin" | "import",
        "platform_username": "username" (for Substack) or "account_id" (for LinkedIn),
        "content_to_analyze": ["bio", "interests", "writing_style"]
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

        # Initialize Supabase client
        supabase = get_supabase_client()

        # For import platform, we don't need to check social connections
        if platform != "import":
            # Verify the social connection exists and is being analyzed
            connection_response = (
                supabase.table("social_connections")
                .select("*")
                .eq("user_id", user_id)
                .eq("platform", platform)
                .execute()
            )

            if not connection_response.data:
                error_msg = f"{platform} connection not found for user {user_id}"
                logger.error(error_msg)
                return (
                    json.dumps({"success": False, "error": error_msg}),
                    404,
                    headers,
                )

            connection = connection_response.data[0]

            if not connection.get("analysis_started_at"):
                error_msg = f"Analysis not started for user {user_id}"
                logger.error(error_msg)
                return (
                    json.dumps({"success": False, "error": error_msg}),
                    400,
                    headers,
                )

        user_preferences_response = (
            supabase.table("user_preferences")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        current_bio = ""
        if user_preferences_response.data:
            current_bio = user_preferences_response.data[0].get("bio", "")

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
                    supabase,
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
                        supabase,
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
