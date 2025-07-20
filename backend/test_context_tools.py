#!/usr/bin/env python3
"""
Test script to verify the context-based tool calling approach.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.services.post_generator import (
    PostGenerationContext,
    generate_linkedin_post_tool,
    revise_linkedin_post_tool,
)
from app.services.model_config import model_config
from pydantic_ai import Agent


async def test_context_based_tools():
    """Test the context-based tool calling approach."""
    print("Testing context-based tool calling...")

    try:
        # Create a context with test data
        context = PostGenerationContext(
            idea_content="Test post about AI in business",
            bio="Software engineer with 5 years experience",
            writing_style="Professional but approachable",
            linkedin_post_strategy="Educational content with personal insights",
            conversation_context="User wants to share their experience with AI tools",
        )

        # Create agent with context-based tools
        agent = Agent[PostGenerationContext, str](
            model_config.get_chat_model(),
            tools=[generate_linkedin_post_tool],
            model_settings=model_config.get_chat_model_settings(),
            output_type=str,
            instructions="""
            You are a LinkedIn content strategist. When the user asks you to create a post,
            use the generate_linkedin_post_tool. The tool has access to all user information
            automatically - you don't need to pass any parameters.
            """,
            retries=1,
        )

        print(f"✓ Agent created with context: {context}")

        # Test the agent
        result = await agent.run("Please create a LinkedIn post for me", deps=context)

        print(f"✓ Agent run successful")
        print(f"Response: {result.output[:100]}...")

        return True

    except Exception as e:
        print(f"✗ Context-based tool test error: {e}")
        print(f"Error type: {type(e)}")

        # Try to get more details
        if hasattr(e, "body"):
            print(f"Error body: {e.body}")

        return False


async def test_simple_agent_without_tools():
    """Test a simple agent without tools to isolate issues."""
    print("\nTesting simple agent without tools...")

    try:
        # Create a simple agent without tools
        agent = Agent[str, str](
            model_config.get_chat_model(),
            model_settings=model_config.get_chat_model_settings(),
            output_type=str,
            instructions="You are a helpful assistant. Respond briefly.",
            retries=1,
        )

        result = await agent.run("Say hello", deps="test")
        print(f"✓ Simple agent run successful: {result.output[:50]}...")

        return True

    except Exception as e:
        print(f"✗ Simple agent test error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=== Context-Based Tool Calling Test ===\n")

    tests = [
        test_simple_agent_without_tools,
        test_context_based_tools,
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
        print("✓ All tests passed! Context-based tool calling should work.")
    else:
        print("✗ Some tests failed. Check the configuration.")
        print("\nIf the simple agent works but context tools fail,")
        print("the issue is likely with the tool calling configuration.")


if __name__ == "__main__":
    asyncio.run(main())
