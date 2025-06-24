#!/usr/bin/env python3
"""
Local testing script for the Substack posts fetcher.

Usage:
    python test_posts_fetcher_local.py [user_id]

Examples:
    python test_posts_fetcher_local.py "user-uuid-here"
"""

import os
import sys
import json
from substack_posts_fetcher import SubstackPostsFetcher
from supabase import create_client


def test_user_suggestions(user_id: str):
    """Test complete user suggestions workflow."""
    print(f"Testing complete user suggestions workflow for user: {user_id}")
    print("-" * 70)

    # Get Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv(
        "SUPABASE_KEY"
    )
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration!")
        print("Required environment variables:")
        print("  SUPABASE_URL - Your Supabase project URL")
        print("  SUPABASE_SERVICE_KEY or SUPABASE_KEY - Supabase key")
        return

    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_service_key)

        # Initialize fetcher with Supabase client
        fetcher = SubstackPostsFetcher(
            supabase_client=supabase, openrouter_api_key=openrouter_api_key
        )

        # Test the complete workflow
        result = fetcher.generate_suggestions_for_user(user_id)

        print("✅ User suggestions generated successfully!")
        print("\n📊 Results Summary:")
        print(f"   • Success: {result.get('success', False)}")
        print(f"   • Total posts: {result.get('total_posts', 0)}")
        print(f"   • Total newsletters: {result.get('total_newsletters', 0)}")
        print(f"   • Active newsletters: {result.get('active_newsletters', 0)}")
        print(f"   • Message: {result.get('message', 'N/A')}")

        # Show user preferences
        user_prefs = result.get("user_preferences", {})
        print("\n👤 User Preferences:")
        print(
            f"   • Topics of interest: {len(user_prefs.get('topics_of_interest', []))}"
        )
        print(f"   • Websites: {len(user_prefs.get('websites', []))}")
        print(f"   • Substacks: {len(user_prefs.get('substacks', []))}")
        print(f"   • Bio length: {len(user_prefs.get('bio', ''))}")

        # Show posts summary
        posts_summary = result.get("posts_summary", {})
        if posts_summary.get("date_range"):
            print("\n📅 Posts Date Range:")
            print(f"   • From: {posts_summary['date_range']['earliest']}")
            print(f"   • To: {posts_summary['date_range']['latest']}")

        # Show sample posts
        latest_posts = result.get("latest_posts", [])
        if latest_posts:
            print("\n📰 Fetched Posts:")
            for i, post in enumerate(latest_posts, 1):
                print(f"\n   📝 Post {i}:")
                print(f"      • Title: {post.get('title', 'N/A')}")
                print(f"      • Date: {post.get('post_date', 'N/A')}")
                print(f"      • Newsletter: {post.get('newsletter_url', 'N/A')}")
                if post.get("subtitle"):
                    print(f"      • Subtitle: {post.get('subtitle')}")

        # Show full JSON for debugging (optional)
        show_json = os.getenv("SHOW_FULL_JSON", "false").lower() == "true"
        if show_json:
            print("\n🔍 Full JSON Response:")
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ User suggestions test failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_posts_fetcher_local.py [user_id]")
        print("\nExamples:")
        print('  python test_posts_fetcher_local.py "user-uuid-here"')
        print("\nEnvironment variables:")
        print("  SHOW_FULL_JSON=true  - Show full JSON response")
        print("  SUPABASE_URL         - Supabase project URL")
        print("  SUPABASE_SERVICE_KEY - Supabase service key")
        print("  SUPABASE_KEY         - Supabase key (alternative)")
        sys.exit(1)

    user_id = sys.argv[1]

    print("🚀 Starting User-Based Substack Test")
    print(f"👤 User ID: {user_id}")
    print("📅 Fetching posts from the last 3 days")
    print("=" * 70)

    test_user_suggestions(user_id)

    print("\n" + "=" * 70)
    print("✅ User test completed!")


if __name__ == "__main__":
    main()
