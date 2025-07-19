import json
import logging
import os
import traceback
import asyncio
from datetime import datetime
from uuid import UUID
import sys

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import functions_framework
from .posts_generator import PostsGenerator
from .article_fetcher import ArticleFetcher
from .database_client import CloudSQLClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, UUID):
            return str(o)
        return super(DateTimeEncoder, self).default(o)


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

    async def run_async():
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

            # Initialize Cloud SQL client
            database_client = CloudSQLClient()

            # Get user preferences
            user_preferences = database_client.get_user_preferences_complete(user_id)

            # Get topics of interest
            topics_of_interest = user_preferences.get("topics_of_interest", [])

            # Get bio
            bio = user_preferences.get("bio", "")

            # Get writing style
            writing_style = database_client.get_writing_style(user_id)

            # Get user ideas
            user_ideas = database_client.get_user_ideas(user_id)
            print(f"Fetched {len(user_ideas)} user ideas for user {user_id}")

            # initialize candidate posts with user ideas first
            candidate_posts = user_ideas

            # Get latest articles suggested by AI and saved in the idea banks
            latest_idea_bank_posts = database_client.get_latest_articles_from_idea_bank(
                user_id
            )

            candidate_posts.extend(latest_idea_bank_posts)

            number_of_posts_to_generate = int(
                os.getenv("NUMBER_OF_POSTS_TO_GENERATE", "5")
            )

            if len(candidate_posts) < (number_of_posts_to_generate * 2):
                logger.debug(
                    f"{len(candidate_posts)} latest articles found from idea banks for user {user_id} fetched in the last 12 hours"
                )
                logger.debug("Fetching more from Substack and websites")

                # Initialize Zyte scraper
                article_fetcher = ArticleFetcher()

                # Get substacks
                substacks = user_preferences.get("substacks", [])

                # Get websites
                websites = user_preferences.get("websites", [])

                fetch_tasks = []
                if substacks:
                    fetch_tasks.append(
                        article_fetcher.fetch_candidate_articles(
                            substacks, topics_of_interest, bio, 10, True
                        )
                    )
                if websites:
                    fetch_tasks.append(
                        article_fetcher.fetch_candidate_articles(
                            websites, topics_of_interest, bio, 20, False
                        )
                    )

                if fetch_tasks:
                    fetched_results = await asyncio.gather(*fetch_tasks)

                    all_new_articles = []
                    for result_list in fetched_results:
                        all_new_articles.extend(result_list)

                    if all_new_articles:
                        saved_posts = (
                            database_client.save_candidate_posts_to_idea_banks(
                                user_id, all_new_articles
                            )
                        )
                        candidate_posts.extend(saved_posts)
                        logger.info(
                            f"Saved {len(saved_posts)} new articles to idea bank."
                        )

            posts_generator = PostsGenerator()

            linkedin_post_strategy = database_client.get_content_strategy(user_id)

            filtered_articles = await posts_generator.filter_articles(
                candidate_posts,
                bio,
                topics_of_interest,
                number_of_posts_to_generate,
            )

            generated_posts = []
            if filtered_articles:
                tasks = [
                    posts_generator.generate_post(
                        article.get("content"),
                        bio,
                        writing_style,
                        linkedin_post_strategy,
                    )
                    for article in filtered_articles
                ]
                generated_post_results = await asyncio.gather(*tasks)

                for i, article in enumerate(filtered_articles):
                    generated_post = generated_post_results[i].model_dump()
                    generated_post["idea_bank_id"] = article.get("id")
                    generated_posts.append(generated_post)

            # Add the post_id and article_url to the generated posts
            for post in generated_posts:
                for candidate_post in candidate_posts:
                    if candidate_post.get("url") == post.get("post_url"):
                        post["post_id"] = candidate_post.get("id").__str__()
                        post["article_url"] = candidate_post.get("url")
                        break

            # save the generated posts to the contents table
            saved_posts = database_client.save_suggested_posts(user_id, generated_posts)

            # update daily suggestions job status
            database_client.update_daily_suggestions_job_status(user_id)

            return (
                json.dumps(saved_posts, indent=2, cls=DateTimeEncoder),
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

    # Handle both sync and async contexts
    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're already in an event loop, create a task
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, run_async())
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(run_async())
