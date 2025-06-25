import json
import logging
import os
import traceback
from typing import Any, Dict, List
from datetime import datetime, timedelta

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
            supabase_client.table("writing_style_analysis")
            .select("analysis_data")
            .eq("user_id", user_id)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0].get("analysis_data", "")
        else:
            logger.info(f"No writing style analysis found for user {user_id}")
            return ""
    except Exception as e:
        logger.error(f"Error fetching user writing style for user {user_id}: {e}")
        # Return empty string instead of raising to allow function to continue
        return ""


def get_latest_linkedin_posts_from_idea_banks(
    supabase_client: Client, user_id: str
) -> List[Dict[str, Any]]:
    """
    Get the latest LinkedIn posts from the idea banks created in the last 12 hours.
    """
    try:
        # Calculate 12 hours ago
        twelve_hours_ago = (datetime.now() - timedelta(hours=12)).isoformat()

        response = (
            supabase_client.table("idea_banks")
            .select("id, data, created_at")
            .eq("user_id", user_id)
            .eq("data->>type", "substack")
            .gte("created_at", twelve_hours_ago)
            .order("created_at", desc=True)
            .execute()
        )
        if response.data:
            logger.info(
                f"Found {len(response.data)} idea bank posts from last 12 hours for user {user_id}"
            )
            return [
                {
                    "id": post["id"],
                    "url": post["data"]["value"],
                    "title": post["data"]["title"],
                }
                for post in response.data
            ]
        else:
            logger.info(
                f"No LinkedIn posts found in idea banks for user {user_id} in the last 12 hours"
            )
            return []
    except Exception as e:
        logger.error(
            f"Error fetching latest LinkedIn posts from idea banks for user {user_id}: {e}"
        )
        return []


def save_candidate_posts_to_idea_banks(
    supabase_client: Client, user_id: str, candidate_posts: List[Dict[str, Any]]
):
    """
    Save candidate posts to idea banks, or get existing ID if URL already exists.
    """
    for i, post in enumerate(candidate_posts):
        post_url = post.get("url")

        # Check if this URL already exists for the user
        existing_response = (
            supabase_client.table("idea_banks")
            .select("id")
            .eq("user_id", user_id)
            .like("data->>value", post_url)
            .execute()
        )

        if existing_response.data:
            # URL already exists, use the existing ID
            existing_id = existing_response.data[0]["id"]
            candidate_posts[i]["id"] = existing_id
            logger.info(
                f"Found existing idea bank entry for user {user_id}, URL {post_url}: {existing_id}"
            )
        else:
            # URL doesn't exist, create new entry
            data = {
                "type": "substack",
                "value": post_url,
                "title": post.get("title", ""),
                "time_sensitive": post.get("time_sensitive", False),
                "ai_suggested": True,
            }
            response = (
                supabase_client.table("idea_banks")
                .insert(
                    {
                        "user_id": user_id,
                        "data": data,
                    }
                )
                .execute()
            )

            if not response.data:
                logger.error(
                    "No data returned when saving candidate post to idea banks"
                )
                raise Exception("No data returned from idea banks insert")
            logger.info(
                f"Saved new candidate post to idea banks for user {user_id}: {response.data}"
            )
            candidate_posts[i]["id"] = response.data[0].get("id")
    return candidate_posts


def save_suggested_posts_to_contents(
    supabase_client: Client, user_id: str, suggested_posts: List[Dict[str, Any]]
):
    """
    Save suggested posts to contents.
    """
    for i, post in enumerate(suggested_posts):
        data = {
            "user_id": user_id,
            "title": post.get("title", None),
            "content": post.get("linkedin_post", ""),
            "platform": "linkedin",
            "status": "suggested",
            "created_at": datetime.now().isoformat(),
            "recommendation_score": post.get("recommendation_score", 50),
            "idea_bank_id": post.get("post_id", None),
            "topics": post.get("topics", []),
        }
        response = supabase_client.table("suggested_posts").insert(data).execute()
        if not response.data:
            logger.error(f"Error saving suggested post to contents: {response.data}")
            raise Exception(f"Failed to save suggested post: {response.data}")
        logger.debug(
            f"Saved suggested post to contents for user {user_id}: {response.data}"
        )
        suggested_posts[i]["post_id"] = response.data[0].get("id")
    return suggested_posts


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

        # Get latest LinkedIn posts from idea banks
        latest_linkedin_posts = get_latest_linkedin_posts_from_idea_banks(
            supabase, user_id
        )

        if len(latest_linkedin_posts) > 0:
            logger.debug(
                f"Found {len(latest_linkedin_posts)} latest LinkedIn posts from idea banks for user {user_id} fetched in the last 12 hours"
            )
            logger.debug("Therefore, skipping Substack posts fetcher")
            candidate_posts = latest_linkedin_posts
        else:
            logger.debug(
                "No latest LinkedIn posts found from idea banks for user {user_id} fetched in the last 12 hours"
            )
            logger.debug("Therefore, using Substack posts fetcher")
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

            # Save candidate posts to idea banks
            candidate_posts = save_candidate_posts_to_idea_banks(
                supabase, user_id, candidate_posts
            )

        posts_generator = PostsGenerator(
            supabase_client=supabase, openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )

        number_of_posts_to_generate = int(os.getenv("NUMBER_OF_POSTS_TO_GENERATE", "3"))

        if len(candidate_posts) < number_of_posts_to_generate:
            # TODO:  get more content from websites or the evergreen topics
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

        # Save generated posts to file
        output_file = f"generated_posts_{len(generated_posts)}_posts.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(generated_posts, f, indent=2, ensure_ascii=False)

        # Add the post_id to the generated posts
        for post in generated_posts:
            for candidate_post in candidate_posts:
                if candidate_post.get("url") == post.get("post_url"):
                    post["post_id"] = candidate_post.get("id")
                    break

        # save the generated posts to the contents table
        saved_posts = save_suggested_posts_to_contents(
            supabase, user_id, generated_posts
        )

        return (
            json.dumps(saved_posts, indent=2),
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
