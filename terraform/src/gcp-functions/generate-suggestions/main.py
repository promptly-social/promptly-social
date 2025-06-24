import json
import logging
import os
import traceback
from typing import Any, Dict

import functions_framework
from supabase import create_client, Client
from substack_posts_fetcher import SubstackPostsFetcher
from posts_generator import PostsGenerator

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


def get_user_preferences_complete(
    supabase_client: Client, user_id: str
) -> Dict[str, Any]:
    """
    Get complete user preferences including all fields.

    Args:
        user_id: The user's ID

    Returns:
        Dictionary containing all user preferences
    """
    if not supabase_client:
        raise ValueError("Supabase client not provided")

    try:
        response = (
            supabase_client.table("user_preferences")
            .select("topics_of_interest, websites, substacks, bio")
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            logger.info(f"No user preferences found for user {user_id}")
            return {
                "topics_of_interest": [],
                "websites": [],
                "substacks": [],
                "bio": "",
            }

        preferences = response.data[0]
        logger.info(
            f"Found user preferences for user {user_id}: {len(preferences.get('substacks', []))} substacks"
        )

        return {
            "topics_of_interest": preferences.get("topics_of_interest", []),
            "websites": preferences.get("websites", []),
            "substacks": preferences.get("substacks", []),
            "bio": preferences.get("bio", ""),
        }

    except Exception as e:
        logger.error(f"Error fetching user preferences for user {user_id}: {e}")
        raise


def get_writing_style(supabase_client: Client, user_id: str) -> str:
    """
    Get the user's writing style.
    """
    if not supabase_client:
        raise ValueError("Supabase client not provided")

    try:
        response = (
            supabase_client.table("user_preferences")
            .select("writing_style")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0].get("writing_style", "")
    except Exception as e:
        logger.error(f"Error fetching user writing style for user {user_id}: {e}")
        raise


@functions_framework.http
def generate_suggestions(request):
    """
    GCP Cloud Function for generating content suggestions based on user preferences.

    Expected request body:
    {
        "user_id": "uuid"
    }

    Returns:
    {
        "success": true,
        "user_preferences": {
            "topics_of_interest": [...],
            "websites": [...],
            "substacks": [...],
            "bio": "..."
        },
        "latest_posts": [
            {
                "url": "...",
                "title": "...",
                "subtitle": "...",
                "author": "...",
                "post_date": "...",
                "newsletter_url": "...",
                "newsletter_name": "...",
                "content_preview": "..."
            }
        ],
        "total_posts": 10,
        "total_newsletters": 5
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

        if not user_id:
            return (
                json.dumps({"success": False, "error": "user_id is required"}),
                400,
                headers,
            )

        logger.info(f"Generating suggestions for user {user_id}")

        # Initialize Supabase client
        supabase = get_supabase_client()

        # Get user preferences
        user_preferences = get_user_preferences_complete(supabase, user_id)

        # Get substacks
        substacks = user_preferences.get("substacks", [])

        # Get topics of interest
        topics_of_interest = user_preferences.get("topics_of_interest", [])

        # Get websites
        # websites = user_preferences.get("websites", [])

        # Get bio
        bio = user_preferences.get("bio", "")

        # Get writing style
        writing_style = get_writing_style(supabase, user_id)

        # Initialize Substack posts fetcher with Supabase client
        posts_fetcher = SubstackPostsFetcher(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        # Generate complete suggestions using the fetcher
        substack_data = posts_fetcher.generate_suggestions_for_user(
            user_id,
            substacks,
            topics_of_interest,
            bio,
        )

        candidate_posts = substack_data.get("latest_posts", [])

        posts_generator = PostsGenerator(
            supabase_client=supabase, openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )

        number_of_posts_to_generate = os.getenv("NUMBER_OF_POSTS_TO_GENERATE")

        if len(candidate_posts) < number_of_posts_to_generate:
            # TODO:  get more content from websites
            pass

        linkedin_post_strategy = """
        Best Practices for Crafting Engaging LinkedIn Post Text
Start with a Strong Hook: Begin the post with a compelling question, a surprising statistic, or a bold statement to immediately capture the reader's attention and stop them from scrolling.
Encourage Conversation: End your post with a clear call-to-action or an open-ended question that prompts readers to share their own experiences, opinions, or advice in the comments. Frame the text to start a discussion, not just to broadcast information.
Write for Readability: Use short paragraphs, single-sentence lines, and bullet points to break up large blocks of text. This makes the post easier to scan and digest on a mobile device.
Provide Genuine Value: The core of the text should offer insights, tips, or a personal story that is valuable to your target audience. Avoid pure self-promotion and focus on sharing expertise or relatable experiences.
Incorporate Strategic Mentions: When mentioning other people or companies, tag them using @. Limit this to a maximum of five relevant tags per post to encourage a response without appearing spammy.
Use Niche Hashtags: Integrate up to three specific and relevant hashtags at the end of your post. These should act as keywords for your topic (e.g., #ProjectManagementTips instead of just #Management) to connect with interested communities.
        """

        generated_posts = posts_generator.generate_posts(
            user_id,
            candidate_posts,
            bio,
            writing_style,
            topics_of_interest,
            number_of_posts_to_generate,
            linkedin_post_strategy,
        )

        return (
            json.dumps(substack_data, indent=2),
            200,
            headers,
        )

    except Exception as e:
        logger.error(f"Error in generate_suggestions function: {e}")
        logger.error(traceback.format_exc())
        return (
            json.dumps({"success": False, "error": str(e)}),
            500,
            headers,
        )
