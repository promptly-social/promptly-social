#!/usr/bin/env python3
"""
Debug script to check OpenRouter configuration and identify issues.
"""

import os
import sys
import asyncio
import httpx

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.core.config import settings


async def check_openrouter_api_key():
    """Check if OpenRouter API key is valid."""
    print("Checking OpenRouter API key...")

    api_key = os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key

    if not api_key or api_key == "dummy-openrouter-api-key":
        print("✗ No valid OpenRouter API key found")
        print("Set OPENROUTER_API_KEY environment variable")
        return False

    print(f"✓ API key found: {api_key[:10]}...")

    # Test API key by calling OpenRouter models endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                print("✓ API key is valid")
                models = response.json()
                print(f"✓ Found {len(models.get('data', []))} available models")
                return True
            else:
                print(f"✗ API key validation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False

    except Exception as e:
        print(f"✗ Error checking API key: {e}")
        return False


async def check_model_availability():
    """Check if the configured models are available."""
    print("\nChecking model availability...")

    api_key = os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key

    if not api_key or api_key == "dummy-openrouter-api-key":
        print("✗ Cannot check models without valid API key")
        return False

    models_to_check = [
        settings.openrouter_model_primary,
        settings.openrouter_large_model_primary,
    ]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )

            if response.status_code != 200:
                print(f"✗ Failed to get models list: {response.status_code}")
                return False

            models_data = response.json()
            available_models = {model["id"] for model in models_data.get("data", [])}

            all_available = True
            for model in models_to_check:
                if model in available_models:
                    print(f"✓ Model available: {model}")
                else:
                    print(f"✗ Model NOT available: {model}")
                    all_available = False

            return all_available

    except Exception as e:
        print(f"✗ Error checking model availability: {e}")
        return False


async def test_simple_openrouter_call():
    """Test a simple OpenRouter API call."""
    print("\nTesting simple OpenRouter API call...")

    api_key = os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key

    if not api_key or api_key == "dummy-openrouter-api-key":
        print("✗ Cannot test without valid API key")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openrouter_model_primary,
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "max_tokens": 10,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                print("✓ Simple API call successful")
                result = response.json()
                content = (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                print(f"✓ Response: {content}")
                return True
            else:
                print(f"✗ API call failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False

    except Exception as e:
        print(f"✗ Error in API call: {e}")
        return False


def check_environment():
    """Check environment configuration."""
    print("\nChecking environment configuration...")

    print(f"Primary model: {settings.openrouter_model_primary}")
    print(f"Large model: {settings.openrouter_large_model_primary}")
    print(f"Temperature: {settings.openrouter_model_temperature}")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        print(f"✓ OPENROUTER_API_KEY environment variable set")
    else:
        print(f"✗ OPENROUTER_API_KEY environment variable not set")
        print(f"Using default from config: {settings.openrouter_api_key}")


async def main():
    """Run all diagnostic checks."""
    print("=== OpenRouter Diagnostic ===\n")

    check_environment()

    tests = [
        check_openrouter_api_key,
        check_model_availability,
        test_simple_openrouter_call,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("✓ All diagnostic checks passed!")
        print("The OpenRouter configuration should work.")
    else:
        print("✗ Some diagnostic checks failed.")
        print("\nNext steps:")
        print("1. Fix any failed checks above")
        print("2. Ensure OPENROUTER_API_KEY is set correctly")
        print("3. Try different model names if models are not available")


if __name__ == "__main__":
    asyncio.run(main())
