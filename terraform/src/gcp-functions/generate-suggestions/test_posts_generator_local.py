#!/usr/bin/env python3
"""
Local test script for PostsGenerator

This script reads the filtered posts JSON file and tests the PostsGenerator
with sample user data.
"""

import json
import os
from typing import List, Dict, Any

from posts_generator import PostsGenerator

# Test variables - modify these as needed
USER_ID = "827b476e-93b2-4a70-8a52-78e8500d26fe"
BIO = """
I'm a founder and CTO, currently building my third AI-native company. My journey has taken me from being a consultant at McKinsey to the founding team of ZestyAI and co-founding Paxton AI. I'm passionate about the practical side of building a business, and my writing explores the intersection of AI, product-led growth (PLG), and founder psychology.

In my 'field notes,' I delve into go-to-market strategies, product development philosophies, and the technical realities of implementing AI. I also reflect on the human side of the startup journey—the tough decisions, the psychological drivers, and how technology shapes our lives. When I'm not working on my next venture, I'm usually exploring the trails around Bend, Oregon with my partner and our two dogs.
"""
WRITING_STYLE = """
The writing style is conversational and analytical, blending personal experience with strategic business and technology insights.

The author grounds complex concepts in a single, powerful, and relatable metaphor that serves as the central theme for the entire post (e.g., "The Bowling Alley" for market entry, "The Chef's Knife vs. The Swiss Army Knife" for product focus).
*   To write like this: Frame your article around a core analogy. Introduce it early and refer back to it to simplify complex points.

The tone is consistently conversational and approachable, often using "I" and directly addressing the reader with "you." This creates the feeling of a knowledgeable peer sharing insights rather than a distant expert lecturing.
*   To write like this: Write as if you are explaining a concept to a smart colleague over coffee. Use personal pronouns and ask rhetorical questions to engage the reader.

Personal anecdotes and stories are used to make abstract topics tangible and relatable. The author connects high-level ideas about AI, business strategy, and psychology to their own life (e.g., getting a tattoo, reflecting on a past company, managing phone use).
*   To write like this: Don't just explain a theory; show how it applies to a real-life situation, preferably one you have personally experienced. This builds credibility and makes the lesson stick.

The voice is authoritative without being arrogant. The author presents well-reasoned arguments and clear opinions, establishing expertise through the quality of the analysis itself.
*   To write like this: State your conclusions clearly and back them up with logical steps or illustrative examples. Avoid hedging language and present your perspective with confidence.

Sentence structure is varied to maintain a dynamic reading pace. Shorter, punchier sentences are often used for emphasis after longer, more explanatory ones.
*   To write like this: Read your work aloud. If it sounds monotonous, break up long sentences and combine short, choppy ones to create a better rhythm.

The author excels at making highly technical or strategic topics (like AI context windows or market segmentation) accessible to a broader audience. This is achieved by avoiding jargon and using simple, clear language.
*   To write like this: Before publishing, have someone outside your field read your draft. If they don't understand a concept, find a simpler way to explain it, often by using an analogy.

Posts are well-structured, often starting with a strong hook or question, developing the idea with clear paragraphs or sections, and ending with a concise summary, a key takeaway, or a forward-looking question.
*   To write like this: Outline your post before you write. Have a clear beginning (the hook), middle (the argument), and end (the conclusion/takeaway). Use subheadings to guide the reader.

The overall personality that emerges is that of a curious and reflective builder. The writing shows a mind that is constantly learning, experimenting, and connecting ideas across different domains like technology, business, and human behavior.
*   To write like this: Share your learning process. Write about your failures and reflections as much as your successes. Connect seemingly unrelated topics to reveal deeper insights.
"""
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
