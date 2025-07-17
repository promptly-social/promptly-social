#!/usr/bin/env python3
"""
Local test script for the share-post Cloud Function.
This script allows you to test the function locally without deploying to GCP.
"""

import json
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Add the current directory to Python path to import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import share_post


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
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
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
    if not os.getenv("LINKEDIN_TOKEN_REFRESH_THRESHOLD"):
        os.environ["LINKEDIN_TOKEN_REFRESH_THRESHOLD"] = "60"
        print("ℹ️  Set LINKEDIN_TOKEN_REFRESH_THRESHOLD to default value: 60")

    if not os.getenv("MAX_RETRY_ATTEMPTS"):
        os.environ["MAX_RETRY_ATTEMPTS"] = "3"
        print("ℹ️  Set MAX_RETRY_ATTEMPTS to default value: 3")

    print("✅ All required environment variables are set")
    return True


def test_share_post(user_id: str, post_id: str):
    """Test the share_post function with specific user and post IDs."""

    print(f"\n🧪 Testing share_post for user: {user_id}, post: {post_id}")
    print("=" * 60)

    # Create mock request
    request_data = {"user_id": user_id, "post_id": post_id}
    mock_request = MockRequest(request_data)

    try:
        # Call the function
        response_data, status_code, headers = share_post(mock_request)

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
            if response_json.get("success"):
                print("\n📈 Summary:")
                print(
                    f"   LinkedIn Post ID: {response_json.get('linkedin_post_id', 'N/A')}"
                )
                print(f"   Shared At: {response_json.get('shared_at', 'N/A')}")
                print(f"   Message: {response_json.get('message', 'N/A')}")

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


def test_error_cases():
    """Test various error scenarios."""
    print("\n🧪 Testing error cases...")
    print("=" * 30)

    # Test with missing user_id
    print("\n🔍 Testing with missing user_id:")
    mock_request = MockRequest({"post_id": "test-post-id"})
    response_data, status_code, headers = share_post(mock_request)
    response = (
        json.loads(response_data) if isinstance(response_data, str) else response_data
    )
    print(f"   Status: {status_code} (expected: 400)")
    print(f"   Error: {response.get('error', 'N/A')}")

    # Test with missing post_id
    print("\n🔍 Testing with missing post_id:")
    mock_request = MockRequest({"user_id": "test-user-id"})
    response_data, status_code, headers = share_post(mock_request)
    response = (
        json.loads(response_data) if isinstance(response_data, str) else response_data
    )
    print(f"   Status: {status_code} (expected: 400)")
    print(f"   Error: {response.get('error', 'N/A')}")

    # Test with invalid JSON
    print("\n🔍 Testing with invalid request:")
    mock_request = MockRequest(None)
    response_data, status_code, headers = share_post(mock_request)
    response = (
        json.loads(response_data) if isinstance(response_data, str) else response_data
    )
    print(f"   Status: {status_code} (expected: 400)")
    print(f"   Error: {response.get('error', 'N/A')}")

    # Test CORS preflight
    print("\n🔍 Testing CORS preflight (OPTIONS):")
    mock_request = MockRequest({}, method="OPTIONS")
    response_data, status_code, headers = share_post(mock_request)
    print(f"   Status: {status_code} (expected: 204)")
    print(f"   CORS Headers: {headers.get('Access-Control-Allow-Origin', 'N/A')}")


def test_with_nonexistent_post():
    """Test with a non-existent post ID."""
    print("\n🔍 Testing with non-existent post:")
    fake_user_id = "00000000-0000-0000-0000-000000000000"
    fake_post_id = "00000000-0000-0000-0000-000000000001"

    response, status = test_share_post(fake_user_id, fake_post_id)

    if status == 404:
        print("✅ Correctly handled non-existent post")
    else:
        print(f"⚠️  Unexpected status for non-existent post: {status}")


def interactive_test():
    """Interactive test mode where user can input their own IDs."""
    print("\n🎯 Interactive Test Mode")
    print("=" * 25)

    try:
        user_id = "1dffd8e7-d135-465d-8a6c-8beed6b1064d"
        post_id = "00000000-0000-0000-0000-000000000001"

        test_share_post(user_id, post_id)

    except Exception as e:
        print(f"❌ Error in interactive test: {e}")


def main():
    """Main function to run the tests."""
    print("🚀 Starting local test for share-post Cloud Function")
    print("=" * 55)

    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Exiting.")
        sys.exit(1)

    # Run error case tests first
    test_error_cases()

    # Test with non-existent post
    test_with_nonexistent_post()

    # Interactive test (optional)
    print("\n" + "=" * 55)
    choice = (
        input("Would you like to run an interactive test with real IDs? (y/N): ")
        .strip()
        .lower()
    )
    if choice in ["y", "yes"]:
        interactive_test()

    print("\n🎉 Local testing completed!")
    print("\n💡 Tips for testing:")
    print("   - Make sure you have a scheduled post in your database")
    print("   - Ensure the user has a valid LinkedIn connection")
    print("   - Check that LinkedIn tokens are not expired")
    print("   - Review the logs for detailed error information")


if __name__ == "__main__":
    main()
