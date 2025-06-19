#!/usr/bin/env python3
"""
Local testing script for the Substack analysis function.

Usage:
    python test_analyzer_local.py [username]

Example:
    python test_analyzer_local.py stratechery
"""

import os
import sys
import json
from substack_analyzer import SubstackAnalyzer


def test_analysis(username: str):
    """Test the Substack analysis locally."""
    print(f"Testing analysis for: {username}")
    print("-" * 50)

    analyzer = SubstackAnalyzer(
        max_posts=5, openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
    )
    try:
        result = analyzer.analyze_substack(username, "")

        print("✅ Analysis completed successfully!")
        print("\n📊 Results Summary:")
        print(f"   • Writing style: {result.get('writing_style', '')}")

        if result.get("topics"):
            print(f"\n🏷️   Topics: {', '.join(result['topics'])}")
        if result.get("websites"):
            print(f"\n🏷️   Websites: {', '.join(result['websites'])}")

        print("\n🔍 Full Analysis (JSON):")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_analyzer_local.py [username]")
        print("Example: python test_analyzer_local.py stratechery")
        sys.exit(1)

    username = sys.argv[1]

    # Set test environment variables if needed

    if not os.getenv("MAX_POSTS_TO_ANALYZE"):
        os.environ["MAX_POSTS_TO_ANALYZE"] = "10"

    test_analysis(username)


if __name__ == "__main__":
    main()
