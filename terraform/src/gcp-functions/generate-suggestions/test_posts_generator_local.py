#!/usr/bin/env python3
"""
Local test script for PostsGenerator

This script reads the filtered posts JSON file and tests the PostsGenerator
with sample user data.
"""

import json
import os
import glob
from typing import List, Dict, Any

from posts_generator import PostsGenerator

# Test variables - modify these as needed
USER_ID = "t827b476e-93b2-4a70-8a52-78e8500d26fe"
BIO = "Tech entrepreneur passionate about AI, startups, and digital transformation. Building the future one line of code at a time."
WRITING_STYLE = "Professional yet approachable, uses storytelling, asks engaging questions, includes relevant hashtags"
TOPICS_OF_INTEREST = [
    "artificial intelligence",
    "startups",
    "technology",
    "entrepreneurship",
    "digital transformation",
]
NUMBER_OF_POSTS_TO_GENERATE = 3
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TEST_POSTS_FILE = "filtered_posts.json"
LINKEDIN_POST_STRATEGY = """
        Best Practices for Crafting Engaging LinkedIn Post Text
Start with a Strong Hook: Begin the post with a compelling question, a surprising statistic, or a bold statement to immediately capture the reader's attention and stop them from scrolling.
Encourage Conversation: End your post with a clear call-to-action or an open-ended question that prompts readers to share their own experiences, opinions, or advice in the comments. Frame the text to start a discussion, not just to broadcast information.
Write for Readability: Use short paragraphs, single-sentence lines, and bullet points to break up large blocks of text. This makes the post easier to scan and digest on a mobile device.
Provide Genuine Value: The core of the text should offer insights, tips, or a personal story that is valuable to your target audience. Avoid pure self-promotion and focus on sharing expertise or relatable experiences.
Incorporate Strategic Mentions: When mentioning other people or companies, tag them using @. Limit this to a maximum of five relevant tags per post to encourage a response without appearing spammy.
Use Niche Hashtags: Integrate up to three specific and relevant hashtags at the end of your post. These should act as keywords for your topic (e.g., #ProjectManagementTips instead of just #Management) to connect with interested communities.
        """


def load_filtered_posts(file_path: str) -> List[Dict[str, Any]]:
    """Load filtered posts from JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        print(f"Loaded {len(posts)} filtered posts")
        return posts

    except Exception as e:
        print(f"Error loading filtered posts: {e}")
        raise


def test_posts_generator():
    """Test the PostsGenerator with local data."""
    print("Starting PostsGenerator test...")

    # Find and load filtered posts
    try:
        candidate_posts = load_filtered_posts(TEST_POSTS_FILE)
    except Exception as e:
        print(f"Error loading posts: {e}")
        return

    if not candidate_posts:
        print("No candidate posts found. Exiting test.")
        return

    # Initialize PostsGenerator (Supabase client can be None for this test)
    generator = PostsGenerator(
        supabase_client=None,  # Not needed for this test
        openrouter_api_key=OPENROUTER_API_KEY,
    )

    print(f"\nTest Configuration:")
    print(f"User ID: {USER_ID}")
    print(f"Bio: {BIO}")
    print(f"Writing Style: {WRITING_STYLE}")
    print(f"Topics of Interest: {TOPICS_OF_INTEREST}")
    print(f"Number of posts to generate: {NUMBER_OF_POSTS_TO_GENERATE}")
    print(f"Candidate posts count: {len(candidate_posts)}")

    # Generate posts
    try:
        print(f"\nGenerating {NUMBER_OF_POSTS_TO_GENERATE} LinkedIn posts...")

        generated_posts = generator.generate_posts(
            user_id=USER_ID,
            candidate_posts=candidate_posts,
            bio=BIO,
            writing_style=WRITING_STYLE,
            topics_of_interest=TOPICS_OF_INTEREST,
            number_of_posts_to_generate=NUMBER_OF_POSTS_TO_GENERATE,
            linkedin_post_strategy=LINKEDIN_POST_STRATEGY,
        )

        # Save generated posts to file
        output_file = f"generated_posts_{USER_ID}_{len(generated_posts)}_posts.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(generated_posts, f, indent=2, ensure_ascii=False)

        print(
            f"\nSuccess! Generated {len(generated_posts) if isinstance(generated_posts, list) else 'unknown'} posts"
        )
        print(f"Results saved to: {output_file}")

        # Display preview of generated posts
        if isinstance(generated_posts, list) and generated_posts:
            print(f"\nPreview of generated posts:")
            for i, post in enumerate(generated_posts[:2], 1):  # Show first 2 posts
                print(f"\n--- Post {i} ---")
                if isinstance(post, dict):
                    print(f"LinkedIn Post: {post.get('linkedin_post', 'N/A')[:200]}...")
                    print(f"Substack URL: {post.get('substack_url', 'N/A')}")
                    print(f"Topics: {post.get('topics', 'N/A')}")
                else:
                    print(f"Post data: {post}")
        else:
            print(f"Generated posts data: {generated_posts}")

    except Exception as e:
        print(f"Error generating posts: {e}")
        raise


if __name__ == "__main__":
    # Check if API key is set
    if OPENROUTER_API_KEY == "your_openrouter_api_key_here":
        print("⚠️  Please set your OPENROUTER_API_KEY in the script before running!")
        print("You can get an API key from: https://openrouter.ai/")
        exit(1)

    test_posts_generator()
