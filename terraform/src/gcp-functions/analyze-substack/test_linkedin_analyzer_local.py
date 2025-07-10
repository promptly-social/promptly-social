#!/usr/bin/env python3
"""
Local testing script for the LinkedIn analysis function.

Usage:
    python test_linkedin_analyzer_local.py [account_id]

Example:
    python test_linkedin_analyzer_local.py linkedin_public_account
"""

import os
import sys
import json
from linkedin_analyzer import LinkedInAnalyzer


def test_analysis(account_id: str):
    """Test the LinkedIn analysis locally."""
    print(f"Testing LinkedIn analysis for account: {account_id}")
    print("-" * 50)

    analyzer = LinkedInAnalyzer(
        max_posts=5,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    try:
        result = analyzer.analyze_linkedin(
            account_id,
            "",
            content_to_analyze=["bio", "writing_style", "interests"],
            # content_to_analyze=["interests"],
        )

        print("✅ LinkedIn analysis completed successfully!")
        print("\n📊 Results Summary:")
        print(f"   • Writing style: {result.get('writing_style', '')}")

        print("\n🔍 Full Analysis (JSON):")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_linkedin_analyzer_local.py [account_id]")
        print("Example: python test_linkedin_analyzer_local.py linkedin_public_account")
        sys.exit(1)

    account_id = sys.argv[1]

    # Set test environment variables if needed
    if not os.getenv("MAX_POSTS_TO_ANALYZE_LINKEDIN"):
        os.environ["MAX_POSTS_TO_ANALYZE_LINKEDIN"] = "5"

    if not os.getenv("APIFY_API_KEY"):
        os.environ["APIFY_API_KEY"] = "apify_api_key"

    test_analysis(account_id)


if __name__ == "__main__":
    main()
