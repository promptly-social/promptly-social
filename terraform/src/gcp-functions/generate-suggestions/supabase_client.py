import os
import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not supabase_url or not supabase_service_key:
            raise ValueError("Missing Supabase configuration")

        self.client: Client = create_client(supabase_url, supabase_service_key)

    def get_user_preferences_complete(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user preferences including all fields.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing all user preferences
        """
        try:
            response = (
                self.client.table("user_preferences")
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

    def get_writing_style(self, user_id: str) -> str:
        """
        Get the user's writing style.
        """
        try:
            response = (
                self.client.table("writing_style_analysis")
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

    def get_user_ideas(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get the user's ideas that either don't have a post yet or the post was generated more than a week ago.
        """
        try:
            # Get ideas with no posts
            ideas_with_no_posts_res = (
                self.client.table("idea_banks")
                .select("id, data, created_at, posts!idea_bank_id!left(id)")
                .eq("user_id", user_id)
                .eq("data->>ai_suggested", "false")
                .is_("posts", "null")
                .execute()
            )
            ideas_with_no_posts = ideas_with_no_posts_res.data or []

            # Get ideas with posts older than a week
            one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            ideas_with_old_posts_res = (
                self.client.table("idea_banks")
                .select("id, data, created_at, posts!idea_bank_id!left(id)")
                .eq("user_id", user_id)
                .eq("data->>ai_suggested", "false")
                .not_.is_("posts", "null")  # Must have posts
                .lt("posts.created_at", one_week_ago)
                .execute()
            )
            ideas_with_old_posts = ideas_with_old_posts_res.data or []

            # Combine and deduplicate
            all_ideas = {idea["id"]: idea for idea in ideas_with_no_posts}
            for idea in ideas_with_old_posts:
                all_ideas[idea["id"]] = idea

            # Sort combined ideas by creation date
            sorted_ideas = sorted(
                all_ideas.values(), key=lambda x: x["created_at"], reverse=True
            )

            return sorted_ideas
        except Exception as e:
            logger.error(f"Error fetching user ideas for user {user_id}: {e}")
            return []

    def get_latest_articles_from_idea_bank(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get the latest articles from the idea banks created in the last 12 hours.
        Args:
            user_id: User ID

        Returns:
            List of idea bank posts
        """
        try:
            # Calculate 12 hours ago
            twelve_hours_ago = (datetime.now() - timedelta(hours=12)).isoformat()

            response = (
                self.client.table("idea_banks")
                .select("id, data, created_at, posts!idea_bank_id!left(id)")
                .eq("user_id", user_id)
                .eq("data->>ai_suggested", "true")
                .gte("created_at", twelve_hours_ago)
                .is_("posts", "null")
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
                        "subtitle": post["data"]["subtitle"],
                        "content": post["data"]["content"],
                        "post_date": post["data"]["post_date"],
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
        self, user_id: str, candidate_posts: List[Dict[str, Any]]
    ):
        """
        Save candidate posts to idea banks, or get existing ID if URL already exists.
        """
        updated_posts = []
        for i, post in enumerate(candidate_posts):
            updated_post = {
                "url": post["url"],
                "title": post["title"],
                "subtitle": post["subtitle"],
                "content": post["content"],
                "post_date": post["post_date"],
            }

            post_url = post["url"]

            # Check if this URL already exists for the user
            existing_response = (
                self.client.table("idea_banks")
                .select("id")
                .eq("user_id", user_id)
                .like("data->>value", post_url)
                .execute()
            )

            if existing_response.data:
                # URL already exists, use the existing ID
                existing_id = existing_response.data[0]["id"]
                updated_post["id"] = existing_id
                logger.info(
                    f"Found existing idea bank entry for user {user_id}, URL {post_url}: {existing_id}"
                )
                updated_posts.append(updated_post)
            else:
                # URL doesn't exist, create new entry
                data = {
                    "value": post_url,
                    "title": post["title"],
                    "subtitle": post["subtitle"],
                    "content": post["content"],
                    "post_date": post["post_date"],
                    "ai_suggested": True,
                }
                response = (
                    self.client.table("idea_banks")
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
                updated_post["id"] = response.data[0].get("id")
                updated_posts.append(updated_post)
        return updated_posts

    def save_suggested_posts(
        self, user_id: str, suggested_posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Save suggested posts to the posts table in Supabase.
        """
        for i, post in enumerate(suggested_posts):
            try:
                data = {
                    "user_id": user_id,
                    "title": post.get("title"),
                    "content": post.get("linkedin_post", ""),
                    "platform": post.get("platform", "linkedin"),
                    "topics": post.get("topics", []),
                    "recommendation_score": post.get("recommendation_score", 0),
                    "status": "suggested",
                    "idea_bank_id": post.get("idea_bank_id"),
                }
                response = self.client.table("posts").insert(data).execute()

                if response.data:
                    logger.info(
                        f"Successfully saved post {i + 1}/{len(suggested_posts)} to posts table"
                    )
                    # Store the post_id in the original data for reference
                    suggested_posts[i]["post_id"] = response.data[0].get("id")
            except Exception as e:
                logger.error(f"Error saving post {i + 1} to database: {e}")
                continue

        return suggested_posts

    def get_content_strategy(self, user_id: str) -> str:
        """
        Get the user's content strategy.
        """
        try:
            response = (
                self.client.table("content_strategies")
                .select("strategy")
                .eq("platform", "linkedin")
                .eq("user_id", user_id)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0].get("strategy", "")
            else:
                logger.info(
                    f"No content strategy found for user {user_id}. So creating one..."
                )
                return self.create_content_strategy(user_id)
        except Exception as e:
            logger.error(
                f"Error fetching user content strategy for user {user_id}: {e}"
            )
            raise

    def create_content_strategy(self, user_id: str) -> str:
        """
        Create a content strategy for the user.
        """
        STRATEGY = """
    Best Practices for Crafting Engaging LinkedIn Post Text
Start with a Strong Hook: Begin the post with a compelling question, a surprising statistic, or a bold statement to immediately capture the reader's attention and stop them from scrolling.
Encourage Conversation: End your post with a clear call-to-action or an open-ended question that prompts readers to share their own experiences, opinions, or advice in the comments. Frame the text to start a discussion, not just to broadcast information.
Write for Readability: Use short paragraphs, single-sentence lines, and bullet points to break up large blocks of text. This makes the post easier to scan and digest on a mobile device.
Provide Genuine Value: The core of the text should offer insights, tips, or a personal story that is valuable to your target audience. Avoid pure self-promotion and focus on sharing expertise or relatable experiences.
Incorporate Strategic Mentions: When mentioning other people or companies, tag them using @. Limit this to a maximum of five relevant tags per post to encourage a response without appearing spammy.
Avoid using hashtags.
    """

        try:
            response = (
                self.client.table("content_strategies")
                .insert(
                    {
                        "user_id": user_id,
                        "platform": "linkedin",
                        "strategy": STRATEGY,
                    }
                )
                .execute()
            )

            if response.data:
                logger.info(f"Created content strategy for user {user_id}")
                return response.data[0].get("strategy", "")
            else:
                logger.error(f"Error creating content strategy for user {user_id}")
                raise Exception("No data returned from content strategies insert")
        except Exception as e:
            logger.error(f"Error creating content strategy for user {user_id}: {e}")
            raise

    def update_daily_suggestions_job_status(self, user_id: str):
        """
        Update the daily suggestions job status for the user.
        """
        try:
            # check if the user has a daily suggestion schedule
            response = (
                self.client.table("daily_suggestion_schedules")
                .select("id")
                .eq("user_id", user_id)
                .execute()
            )

            if (
                not response.data
                or len(response.data) == 0
                or not response.data[0].get("id")
            ):
                logger.info(
                    f"No daily suggestion schedule found for user {user_id}. So creating one..."
                )
                return

            # update the last run at time
            response = (
                self.client.table("daily_suggestion_schedules")
                .update(
                    {
                        "last_run_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .eq("id", response.data[0].get("id"))
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                logger.error(
                    f"Error updating daily suggestions job status for user {user_id}"
                )
                raise Exception("No data returned from daily suggestions jobs update")

            logger.info(f"Updated daily suggestions job status for user {user_id}")
        except Exception as e:
            logger.error(
                f"Error updating daily suggestions job status for user {user_id}: {e}"
            )
            raise
