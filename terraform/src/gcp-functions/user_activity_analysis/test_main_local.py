#!/usr/bin/env python3
"""
Local test script for the user_activity_analysis Cloud Function.
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

from main import user_activity_analysis


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
        "CLOUD_SQL_INSTANCE_CONNECTION_NAME",
        "CLOUD_SQL_DATABASE_NAME", 
        "CLOUD_SQL_USER",
        "CLOUD_SQL_PASSWORD",
        "OPENROUTER_API_KEY",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment.")
        print("\nExample .env file:")
        print("CLOUD_SQL_INSTANCE_CONNECTION_NAME=your-project:region:instance-name")
        print("CLOUD_SQL_DATABASE_NAME=your-database-name")
        print("CLOUD_SQL_USER=your-db-user")
        print("CLOUD_SQL_PASSWORD=your-db-password")
        print("OPENROUTER_API_KEY=your-openrouter-api-key")
        return False

    print("✅ All required environment variables are set")
    return True


def test_user_activity_analysis_sync(config: Dict[str, Any] = None):
    """Test the user_activity_analysis function with optional configuration (synchronous version)."""

    print(f"\n🧪 Testing user_activity_analysis function")
    print("=" * 50)

    # Create mock request with optional configuration
    request_data = config or {}
    mock_request = MockRequest(request_data)

    try:
        # Call the function (this is synchronous despite internal async operations)
        response_data, status_code, headers = user_activity_analysis(mock_request)

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
            if response_json.get("success") and response_json.get("analysis_summary"):
                summary = response_json["analysis_summary"]
                print("\n📈 Analysis Summary:")
                print(f"   Total users processed: {summary.get('total_users_processed', 0)}")
                print(f"   Successful analyses: {summary.get('successful_analyses', 0)}")
                print(f"   Failed analyses: {summary.get('failed_analyses', 0)}")
                print(f"   Skipped analyses: {summary.get('skipped_analyses', 0)}")
                print(f"   Processing time: {summary.get('total_processing_time_seconds', 0):.2f} seconds")

        else:
            print(f"❌ Function failed with status {status_code}")
            if response_json.get("error"):
                print(f"   Error: {response_json['error']}")
                print(f"   Error Type: {response_json.get('error_type', 'unknown')}")

        return response_json, status_code

    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, 500


def test_health_check_sync():
    """Test the health check endpoint (synchronous version)."""
    print("\n🏥 Testing health check endpoint...")
    print("=" * 30)

    try:
        # Import health_check function
        from main import health_check

        mock_request = MockRequest({}, method="GET")
        response_data, status_code, headers = health_check(mock_request)

        if isinstance(response_data, str):
            response_json = json.loads(response_data)
        else:
            response_json = response_data

        print(f"📊 Status Code: {status_code}")
        print("📄 Health Check Response:")
        print(json.dumps(response_json, indent=2))

        if status_code == 200:
            print("✅ Health check passed!")
        else:
            print(f"❌ Health check failed with status {status_code}")

    except Exception as e:
        print(f"💥 Health check exception: {str(e)}")


def main():
    """Main function to run the tests."""
    print("🚀 Starting local test for user_activity_analysis Cloud Function")
    print("=" * 60)

    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Exiting.")
        sys.exit(1)

    # Test health check first
    test_health_check_sync()

    # Run the main test with default configuration
    print("\n🧪 Testing with default configuration...")
    response, status = test_user_activity_analysis_sync()

    # Test with custom configuration
    print("\n🧪 Testing with custom configuration...")
    custom_config = {
        "post_threshold": 3,
        "message_threshold": 8,
        "batch_timeout_minutes": 10,
        "max_users_per_batch": 50
    }
    response, status = test_user_activity_analysis_sync(custom_config)

    # Test error cases
    print("\n🧪 Testing error cases...")
    print("=" * 30)

    # Test with invalid configuration
    print("\n🔍 Testing with invalid post_threshold:")
    invalid_config = {"post_threshold": -1}
    mock_request = MockRequest(invalid_config)
    response_data, status_code, headers = user_activity_analysis(mock_request)
    print(f"   Status: {status_code} (expected: 400)")

    # Test with invalid message_threshold
    print("\n🔍 Testing with invalid message_threshold:")
    invalid_config = {"message_threshold": "invalid"}
    mock_request = MockRequest(invalid_config)
    response_data, status_code, headers = user_activity_analysis(mock_request)
    print(f"   Status: {status_code} (expected: 400)")

    # Test CORS preflight request
    print("\n🔍 Testing CORS preflight request:")
    mock_request = MockRequest({}, method="OPTIONS")
    response_data, status_code, headers = user_activity_analysis(mock_request)
    print(f"   Status: {status_code} (expected: 204)")
    print(f"   CORS Headers: {headers.get('Access-Control-Allow-Origin', 'Missing')}")

    print("\n🎉 Local testing completed!")


if __name__ == "__main__":
    main()
