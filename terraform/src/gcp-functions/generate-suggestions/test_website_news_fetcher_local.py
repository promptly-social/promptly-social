#!/usr/bin/env python3
"""
Test script for WebsiteNewsFetcher with Brave Search and Zyte APIs
"""

import os
from dotenv import load_dotenv
from website_news_fetcher import WebsiteNewsFetcher

# Load environment variables
load_dotenv()


def test_website_news_fetcher():
    """Test the WebsiteNewsFetcher with real APIs"""

    # Initialize the fetcher
    fetcher = WebsiteNewsFetcher(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        zyte_api_key=os.getenv("ZYTE_API_KEY"),
        max_workers=2,
    )

    # Test websites
    website_urls = ["https://tldr.tech"]

    # User preferences
    user_topics_of_interest = [
        "Data",
        "Climate Tech",
        "Software Engineering",
        "Product Design",
        "Business",
        "Ethics",
        "Data Science",
        "Marketing",
        "Startups",
        "Venture Capital",
        "Finance",
        "Business Strategy",
        "Machine Learning",
        "Creator Economy",
        "Design",
        "Digital Marketing",
        "ChatGPT",
        "Product Management",
        "Software Development",
        "AI",
        "Technology",
        "Education",
        "Career",
        "Career Development",
        "Mental Health",
    ]

    bio = """
    I'm a co-founder and CTO, currently building my third AI startup in stealth mode. My journey includes co-founding Paxton AI and being part of the founding team at ZestyAI, alongside a background at McKinsey. I'm deeply passionate about the intersection of AI, product-led growth (PLG), and the psychology behind building and scaling ventures. My writing often explores these themes, offering field notes on everything from market segmentation and audience building to the practical applications and ethical considerations of AI. I'm fascinated by how AI is shaping our world, from its impact on business strategies like Shopify's big AI bet to the more personal ways it can assist, like helping me choose tattoos. I also enjoy reflecting on the journey of entrepreneurship and the decisions that shape it. When I'm not immersed in the world of AI and startups, I'm exploring Bend, OR with my husband and our two dogs.
    """

    print("Testing WebsiteNewsFetcher with Zyte APIs")
    print("=" * 60)

    # Test the main fetch_news method
    try:
        articles = fetcher.fetch_news(website_urls, user_topics_of_interest, bio)

        print(f"Found {len(articles)} relevant articles:")
        print("-" * 40)

        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.get('title', 'No title')}")
            print(f"   URL: {article.get('url', 'No URL')}")
            print(f"   Date: {article.get('post_date', 'No date')}")
            print(f"   Time Sensitive: {article.get('time_sensitive', False)}")
            # Show first 200 characters of content
            content = article.get("content", "")
            if content:
                print(f"   Content: {content[:200]}...")
            else:
                print("   Content: No content available")

    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("WebsiteNewsFetcher Test Suite")
    print("=" * 60)

    # Check if API keys are available
    api_keys = {
        "ZYTE_API_KEY": os.getenv("ZYTE_API_KEY"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
    }

    print("API Key Status:")
    for key, value in api_keys.items():
        status = "✓ Available" if value else "✗ Missing"
        print(f"  {key}: {status}")

    print()

    if all(api_keys.values()):
        test_website_news_fetcher()
    else:
        print("Skipping full integration test - not all API keys available")
        print("Please set ZYTE_API_KEY, and OPENROUTER_API_KEY in your .env file")
