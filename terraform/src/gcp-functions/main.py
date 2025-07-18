"""
Main entry point for Google Cloud Functions.
This file imports and exposes functions from subdirectories.
"""

# Import functions from subdirectories
try:
    from analyze.main import analyze
except ImportError:
    analyze = None

try:
    from generate_suggestions.main import generate_suggestions
except ImportError:
    generate_suggestions = None

try:
    from unified_post_scheduler.main import process_scheduled_posts
except ImportError:
    process_scheduled_posts = None

# Export functions for Google Cloud Functions
__all__ = ["analyze", "generate_suggestions", "process_scheduled_posts"]
