import os
import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.cloud_sql_client import get_cloud_sql_client

logger = logging.getLogger(__name__)


class CloudSQLClient:
    def __init__(self):
        """Initialize Cloud SQL client."""
        self.client = get_cloud_sql_client()

    def get_user_preferences_complete(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user preferences including all fields.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing all user preferences
        """
        try:
            query = """
                SELECT topics_of_interest, websites, substacks, bio 
                FROM user_preferences 
                WHERE user_id = :user_id
            """

            results = self.client.execute_query(query, {"user_id": user_id})

            if not results:
                logger.info(f"No user preferences found for user {user_id}")
                return {
                    "topics_of_interest": [],
                    "websites": [],
                    "substacks": [],
                    "bio": "",
                }

            preferences = results[0]
            logger.info(
                f"Found user preferences for user {user_id}: {len(preferences.get('substacks', []) or [])} substacks"
            )

            return {
                "topics_of_interest": preferences.get("topics_of_interest", []) or [],
                "websites": preferences.get("websites", []) or [],
                "substacks": preferences.get("substacks", []) or [],
                "bio": preferences.get("bio", "") or "",
            }

        except Exception as e:
            logger.error(f"Error fetching user preferences for user {user_id}: {e}")
            raise

    def get_writing_style(self, user_id: str) -> str:
        """
        Get the user's writing style.
        """
        try:
            query = """
                SELECT analysis_data 
                FROM writing_style_analysis 
                WHERE user_id = :user_id
                LIMIT 1
            """

            results = self.client.execute_query(query, {"user_id": user_id})

            if results:
                return results[0].get("analysis_data", "") or ""
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
            # Get ideas with no posts or posts older than a week
            query = """
                SELECT DISTINCT ib.id, ib.data, ib.created_at
                FROM idea_banks ib
                LEFT JOIN posts p ON ib.id = p.idea_bank_id
                WHERE ib.user_id = :user_id 
                  AND (ib.data->>'ai_suggested')::boolean = false
                  AND (p.id IS NULL)
                ORDER BY ib.created_at DESC
            """

            results = self.client.execute_query(
                query, {"user_id": user_id}
            )

            idea_results = results if results else []
 
            ideas = []
            
            for result in idea_results:
                ideas.append({
                    "id": result['id'],
                    "content": result["data"]["value"]
                })

            return ideas
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
            twelve_hours_ago = datetime.now() - timedelta(hours=12)

            query = """
                SELECT ib.id, ib.data, ib.created_at
                FROM idea_banks ib
                LEFT JOIN posts p ON ib.id = p.idea_bank_id
                WHERE ib.user_id = :user_id 
                  AND (ib.data->>'ai_suggested')::boolean = true
                  AND ib.created_at >= :twelve_hours_ago
                  AND p.id IS NULL
                ORDER BY ib.created_at DESC
            """

            results = self.client.execute_query(
                query, {"user_id": user_id, "twelve_hours_ago": twelve_hours_ago}
            )

            if results:
                logger.info(
                    f"Found {len(results)} idea bank posts from last 12 hours for user {user_id}"
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
                    for post in results
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
            existing_query = """
                SELECT id FROM idea_banks 
                WHERE user_id = :user_id AND data->>'value' = :post_url
            """

            existing_results = self.client.execute_query(
                existing_query, {"user_id": user_id, "post_url": post_url}
            )

            if existing_results:
                # URL already exists, use the existing ID
                existing_id = existing_results[0]["id"]
                updated_post["id"] = existing_id
                logger.info(
                    f"Found existing idea bank entry for user {user_id}, URL {post_url}: {existing_id}"
                )
                updated_posts.append(updated_post)
            else:
                # URL doesn't exist, create new entry
                import json

                data = {
                    "value": post_url,
                    "title": post["title"],
                    "subtitle": post["subtitle"],
                    "content": post["content"],
                    "post_date": post["post_date"],
                    "ai_suggested": True,
                }

                insert_query = """
                    INSERT INTO idea_banks (user_id, data)
                    VALUES (:user_id, :data)
                    RETURNING id
                """

                insert_results = self.client.execute_query(
                    insert_query, {"user_id": user_id, "data": json.dumps(data)}
                )

                if not insert_results:
                    logger.error(
                        "No data returned when saving candidate post to idea banks"
                    )
                    raise Exception("No data returned from idea banks insert")

                print(
                    f"Saved new candidate post to idea banks for user {user_id}: {insert_results}"
                )
                updated_post["id"] = insert_results[0]["id"]
                updated_posts.append(updated_post)
        return updated_posts

    def save_suggested_posts(
        self, user_id: str, suggested_posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Save suggested posts to the posts table.
        """
        for i, post in enumerate(suggested_posts):
            try:
                insert_query = """
                    INSERT INTO posts (user_id, title, content, platform, topics, status, idea_bank_id, article_url)
                    VALUES (:user_id, :title, :content, :platform, :topics, :status, :idea_bank_id, :article_url)
                    RETURNING id
                """

                results = self.client.execute_query(
                    insert_query,
                    {
                        "user_id": user_id,
                        "title": post.get("title"),
                        "content": post.get("linkedin_post", ""),
                        "platform": post.get("platform", "linkedin"),
                        "topics": post.get(
                            "topics", []
                        ),  # Pass as Python list for PostgreSQL array
                        "status": "suggested",
                        "idea_bank_id": post.get("idea_bank_id"),
                        "article_url": post.get("post_url"),
                    },
                )

                if results:
                    logger.info(
                        f"Successfully saved post {i + 1}/{len(suggested_posts)} to posts table"
                    )
                    # Store the post_id in the original data for reference
                    suggested_posts[i]["post_id"] = results[0]["id"]
            except Exception as e:
                logger.error(f"Error saving post {i + 1} to database: {e}")
                continue

        return suggested_posts

    def get_content_strategy(self, user_id: str) -> str:
        """
        Get the user's content strategy.
        """
        try:
            query = """
                SELECT strategy 
                FROM content_strategies 
                WHERE user_id = :user_id AND platform = 'linkedin'
                LIMIT 1
            """

            results = self.client.execute_query(query, {"user_id": user_id})

            if results:
                return results[0].get("strategy", "") or ""
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
        STRATEGY = """CORE MESSAGE & TONE:
Focus on a central theme in the post
The tone should be authentic and human. It should feel like a real person sharing a genuine experience or insight, not like corporate marketing copy. Incorporate a mix of sentiment; for example, if discussing a success, first touch upon the struggle or failure that preceded it.

FORMATTING & CONSTRAINTS:
Avoid using hashtags.
Links: ABSOLUTELY NO external links in the body of the post.
Emojis: Use emojis very sparingly. A maximum of one emoji to set the tone is sufficient.   
Engagement Bait: Do not use any phrases that explicitly ask for likes, follows, or simple comments (e.g., "Like this post if..."). The question at the end should be for genuine discussion.   

POST STRUCTURE & CONTENT:
The Hook (First 1-2 Lines):
This is the most critical part. It must be a "scroll-stopper" that creates immediate curiosity, tension, or challenges a common belief.   

Choose one of these proven hook styles:
Contrarian Opinion: "Stop hiring for [common practice]. Here's why."
Relatable Pain Point: "You spent 40 hours on a proposal. They ghosted you."
Shock Value / Story Teaser: "I almost shut down my business last week."
Counter-Intuitive Idea: "My biggest career mistake was taking the promotion."

The Body (Main Content):
Keep the entire post concise, between 150 and 200 words.   
Structure it for maximum scannability on a mobile phone. This means:
Using very short paragraphs (2-3 lines MAXIMUM).
Using plenty of line breaks for white space.   
Tell a story or provide clear, actionable value. Avoid generic advice.

The Call-to-Action (CTA - The Final Line):
End with a specific, open-ended question that demands a story or a detailed opinion from the reader. This is crucial for generating the long, thoughtful comments the algorithm rewards.   

DO NOT use low-effort questions like "Thoughts?", "Do you agree?", or "What do you think?".

INSTEAD, use high-effort questions like:
"What's the worst piece of career advice you've ever received?"
"What's the biggest lesson you learned from a project that failed?"
"What's one thing you wish you knew when you started your career in [your industry]?"
"""

        try:
            insert_query = """
                INSERT INTO content_strategies (user_id, platform, strategy)
                VALUES (:user_id, :platform, :strategy)
                RETURNING strategy
            """

            results = self.client.execute_query(
                insert_query,
                {"user_id": user_id, "platform": "linkedin", "strategy": STRATEGY},
            )

            if results:
                logger.info(f"Created content strategy for user {user_id}")
                return results[0].get("strategy", "")
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
            # Check if the user has a daily suggestion schedule
            check_query = """
                SELECT id FROM daily_suggestion_schedules 
                WHERE user_id = :user_id
                LIMIT 1
            """

            results = self.client.execute_query(check_query, {"user_id": user_id})

            if not results:
                logger.info(
                    f"No daily suggestion schedule found for user {user_id}. So creating one..."
                )
                return

            # Update the last run at time
            update_query = """
                UPDATE daily_suggestion_schedules 
                SET last_run_at = NOW(), updated_at = NOW()
                WHERE user_id = :user_id
            """

            rows_affected = self.client.execute_update(
                update_query, {"user_id": user_id}
            )

            if rows_affected == 0:
                logger.error(
                    f"Error updating daily suggestions job status for user {user_id}"
                )
                raise Exception("No rows updated in daily suggestions jobs update")

            logger.info(f"Updated daily suggestions job status for user {user_id}")
        except Exception as e:
            logger.error(
                f"Error updating daily suggestions job status for user {user_id}: {e}"
            )
            raise
