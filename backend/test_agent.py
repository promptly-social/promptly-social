#!/usr/bin/env python3
"""
Simple test script to verify agent creation and basic functionality.
Run this to test if the PydanticAI configuration is working correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.services.model_config import model_config
from app.services.post_generator import (
    PostGeneratorService,
    generate_linkedin_post_tool,
)
from pydantic_ai import Agent


async def test_model_config():
    """Test the model configuration."""
    print("Testing model configuration...")

    try:
        chat_model = model_config.get_chat_model()
        large_model = model_config.get_large_model()
        chat_settings = model_config.get_chat_model_settings()
        large_settings = model_config.get_large_model_settings()

        print(f"✓ Chat model: {chat_model}")
        print(f"✓ Large model: {large_model}")
        print(f"✓ Chat settings: {chat_settings}")
        print(f"✓ Large settings: {large_settings}")

    except Exception as e:
        print(f"✗ Model config error: {e}")
        return False

    return True


async def test_agent_creation():
    """Test agent creation."""
    print("\nTesting agent creation...")

    try:
        # Test PostGeneratorService
        service = PostGeneratorService()
        print(f"✓ PostGeneratorService created")

        # Test simple agent creation
        agent = Agent[PostGeneratorService, str](
            model_config.get_chat_model(),
            tools=[generate_linkedin_post_tool],
            model_settings=model_config.get_chat_model_settings(),
            output_type=str,
            instructions="You are a helpful assistant.",
            retries=1,
        )
        print("✓ Agent created successfully")

    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        return False

    return True


async def test_simple_run():
    """Test a simple agent run without tools."""
    print("\nTesting simple agent run...")

    try:
        # Create a simple agent without tools first
        agent = Agent[str, str](
            model_config.get_chat_model(),
            model_settings=model_config.get_chat_model_settings(),
            output_type=str,
            instructions="You are a helpful assistant. Respond briefly.",
            retries=1,
        )

        result = await agent.run("Say hello", deps="test")
        print(f"✓ Simple run successful: {result.output[:50]}...")

    except Exception as e:
        print(f"✗ Simple run error: {e}")
        return False

    return True


async def main():
    """Run all tests."""
    print("=== PydanticAI Configuration Test ===\n")

    tests = [
        test_model_config,
        test_agent_creation,
        test_simple_run,
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
        print("✓ All tests passed! The configuration should work.")
    else:
        print("✗ Some tests failed. Check the configuration.")


if __name__ == "__main__":
    asyncio.run(main())
