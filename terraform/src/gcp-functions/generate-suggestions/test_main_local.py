#!/usr/bin/env python3
"""
Local test script for the generate_suggestions Cloud Function.
This script allows you to test the function locally without deploying to GCP.
"""

import json
import os
import sys
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Add the current directory to Python path to import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import generate_suggestions


class MockRequest:
    """Mock request object to simulate Flask request."""

    def __init__(self, json_data: Dict[str, Any], method: str = "POST"):
        self.json_data = json_data
        self.method = method

    def get_json(self, silent=True):
        return self.json_data


def setup_environment():
    """Setup environment variables for local testing."""
    # Load environment variables from .env file if it exists
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print("✅ Loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found. Please ensure environment variables are set.")

    # Check required environment variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "OPENROUTER_API_KEY",
        "ZYTE_API_KEY",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment.")
        return False

    # Set default for optional variables
    if not os.getenv("NUMBER_OF_POSTS_TO_GENERATE"):
        os.environ["NUMBER_OF_POSTS_TO_GENERATE"] = "1"
        print("ℹ️  Set NUMBER_OF_POSTS_TO_GENERATE to default value: 5")

    print("✅ All required environment variables are set")
    return True


async def test_generate_suggestions(user_id: str):
    """Test the generate_suggestions function with a specific user ID."""

    print(f"\n🧪 Testing generate_suggestions for user: {user_id}")
    print("=" * 50)

    # Create mock request
    request_data = {"user_id": user_id}
    mock_request = MockRequest(request_data)

    try:
        # Call the function
        response_data, status_code, headers = await generate_suggestions(mock_request)

        # Parse response
        if isinstance(response_data, str):
            response_json = json.loads(response_data)
        else:
            response_json = response_data

        print(f"📊 Status Code: {status_code}")
        print(f"📋 Headers: {headers}")
        print("📄 Response:")
        print(json.dumps(response_json, indent=2))

        if status_code == 200:
            print("✅ Function executed successfully!")

            # Print summary if successful
            if isinstance(response_json, list) and len(response_json) > 0:
                print("\n📈 Summary:")
                print(f"   Generated posts: {len(response_json)}")
                for i, post in enumerate(response_json[:3]):  # Show first 3 posts
                    print(f"   Post {i + 1}: {post.get('title', 'No title')[:50]}...")

        else:
            print(f"❌ Function failed with status {status_code}")
            if response_json.get("error"):
                print(f"   Error: {response_json['error']}")

        return response_json, status_code

    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback

        traceback.print_exc()
        return None, 500


async def main():
    """Main function to run the tests."""
    print("🚀 Starting local test for generate_suggestions Cloud Function")
    print("=" * 60)

    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Exiting.")
        sys.exit(1)

    test_user_id = "1dffd8e7-d135-465d-8a6c-8beed6b1064d"
    # Run the main test
    response, status = await test_generate_suggestions(test_user_id)

    # Test error cases
    print("\n🧪 Testing error cases...")
    print("=" * 30)

    # Test with missing user_id
    print("\n🔍 Testing with missing user_id:")
    mock_request = MockRequest({})
    response_data, status_code, headers = await generate_suggestions(mock_request)
    print(f"   Status: {status_code} (expected: 400)")

    # Test with invalid JSON
    print("\n🔍 Testing with invalid request:")
    mock_request = MockRequest(None)
    response_data, status_code, headers = await generate_suggestions(mock_request)
    print(f"   Status: {status_code} (expected: 400)")

    print("\n🎉 Local testing completed!")


if __name__ == "__main__":
    asyncio.run(main())
