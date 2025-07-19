"""
Main entry point for Google Cloud Functions.
This file imports and exposes functions from subdirectories.
"""

import sys
import os
import traceback

# Add current directory to Python path to ensure subdirectories can be imported
sys.path.insert(0, os.path.dirname(__file__))

# Import functions from subdirectories
try:
    from analyze.main import analyze
except ImportError as e:
    print(f"Failed to import analyze function: {e}")
    traceback.print_exc()
    analyze = None

try:
    from generate_suggestions.main import generate_suggestions
except ImportError as e:
    print(f"Failed to import generate_suggestions function: {e}")
    traceback.print_exc()
    generate_suggestions = None

try:
    from unified_post_scheduler.main import process_scheduled_posts
except ImportError as e:
    print(f"Failed to import process_scheduled_posts function: {e}")
    traceback.print_exc()
    process_scheduled_posts = None

# Export functions for Google Cloud Functions
__all__ = ["analyze", "generate_suggestions", "process_scheduled_posts"]
