#!/usr/bin/env python3
"""
Test script to verify OpenRouter configuration and basic functionality.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.services.model_config import model_config
from pydantic_ai import Agent


async def test_basic_openrouter_connection():
    """Test basic OpenRouter connection without tools."""
    print("Testing basic OpenRouter connection...")

    try:
        # Create a simple agent without tools
        agent = Agent[str, str](
            model_config.get_chat_model(),
            model_settings=model_config.get_chat_model_settings(),
            output_type=str,
            instructions="You are a helpful assistant. Respond briefly.",
        )

        print(f"✓ Agent created with model: {agent.model}")

        # Test a simple run
        result = await agent.run("Say hello", deps="test")
        print(f"✓ Simple run successful: {result.output[:50]}...")

        return True

    except Exception as e:
        print(f"✗ OpenRouter connection error: {e}")
        print(f"Error type: {type(e)}")

        # Try to get more details
        if hasattr(e, "response"):
            print(f"Response status: {getattr(e.response, 'status_code', 'Unknown')}")
            print(f"Response text: {getattr(e.response, 'text', 'Unknown')}")

        return False


async def test_model_settings():
    """Test model settings configuration."""
    print("\nTesting model settings...")

    try:
        chat_model = model_config.get_chat_model()
        large_model = model_config.get_large_model()
        chat_settings = model_config.get_chat_model_settings()
        large_settings = model_config.get_large_model_settings()

        print(f"✓ Chat model: {chat_model}")
        print(f"✓ Large model: {large_model}")
        print(f"✓ Chat settings: {chat_settings}")
        print(f"✓ Large settings: {large_settings}")

        return True

    except Exception as e:
        print(f"✗ Model settings error: {e}")
        return False


async def test_with_fallback_disabled():
    """Test with fallback models disabled."""
    print("\nTesting with fallback disabled...")

    try:
        from pydantic_ai.models.openai import OpenAIModelSettings

        # Create agent with no fallback models
        agent = Agent[str, str](
            model_config.get_chat_model(),
            model_settings=OpenAIModelSettings(
                temperature=0.0,
                # No extra_body with fallback models
            ),
            output_type=str,
            instructions="You are a helpful assistant. Respond briefly.",
        )

        result = await agent.run("Say hello", deps="test")
        print(f"✓ No-fallback run successful: {result.output[:50]}...")

        return True

    except Exception as e:
        print(f"✗ No-fallback test error: {e}")
        return False


async def main():
    """Run all OpenRouter tests."""
    print("=== OpenRouter Configuration Test ===\n")

    tests = [
        test_model_settings,
        test_with_fallback_disabled,
        test_basic_openrouter_connection,
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
        print("✓ All OpenRouter tests passed!")
    else:
        print("✗ Some OpenRouter tests failed.")
        print("\nTroubleshooting suggestions:")
        print("1. Check your OPENROUTER_API_KEY environment variable")
        print("2. Verify the API key is valid on OpenRouter dashboard")
        print("3. Check if the model names are available in your OpenRouter account")
        print("4. Try with different model names")


if __name__ == "__main__":
    asyncio.run(main())
