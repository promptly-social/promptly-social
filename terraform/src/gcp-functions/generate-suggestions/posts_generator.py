from typing import Any, Dict, List
from datetime import datetime

from openai import OpenAI
from supabase import Client
from helper import extract_json_from_llm_response


class PostsGenerator:
    def __init__(self, supabase_client: Client, openrouter_api_key: str):
        self.supabase_client = supabase_client
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

    def generate_posts(
        self,
        user_id: str,
        candidate_posts: List[Dict[str, Any]],
        bio: str,
        writing_style: str,
        topics_of_interest: List[str],
        number_of_posts_to_generate: int,
        linkedin_post_strategy: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate posts for the user.
        """

        urls = [post["url"] for post in candidate_posts if post.get("url")]

        today = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""
        You are an expert at generating posts for LinkedIn to gain the most engagement using the user's bio, writing style, and topics of interest.
        You are given a list of post URLs.
        Do not include special characters in the posts that people suspect that you are using AI to generate, such as em-dash, arrows, etc.
        You are to generate {number_of_posts_to_generate} posts for the user to pick from and post on LinkedIn.
        The posts should be linkedin appropriate and gain the most engagement. 
        Make sure to cite the substack post or include a link to the substack post in the linkedin posts.
        Generate a recommendation score for the post between 0 and 100, where 100 is the most recommended and 0 is the least recommended.
        The user's bio is: {bio}
        The user's writing style is: {writing_style}
        The user's topics of interest are: {topics_of_interest}
        The post URLs are: {urls}
        The linkedin post strategy for gettting the most engagement is: {linkedin_post_strategy}
        Today's date is: {today}
        Return the posts in a JSON format with the following fields: 
        {{"linkedin_post": "your generated post", "post_id": "the substack post ID that you used to generate the post", "topics": ["topic1", "topic2", "topic3"], "recommendation_score": 0-100}}
        """
        response = self.openrouter_client.chat.completions.create(
            model="google/gemini-2.5-pro",
            extra_body={
                "models": ["openai/gpt-4o"],
            },
            messages=[{"role": "user", "content": prompt}],
        )

        return extract_json_from_llm_response(response.choices[0].message.content)
