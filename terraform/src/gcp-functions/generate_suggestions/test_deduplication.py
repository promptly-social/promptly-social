#!/usr/bin/env python3
"""
Test script for the deduplication functionality in main.py
"""

import sys
import os
from uuid import UUID

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from main import remove_duplicate_posts


def test_remove_duplicate_posts():
    """Test the remove_duplicate_posts function with various scenarios."""
    
    print("Testing remove_duplicate_posts function...")
    
    # Test 1: No duplicates
    print("\n1. Testing with no duplicates:")
    posts_no_duplicates = [
        {"id": "1", "title": "Article 1", "content": "Content 1"},
        {"id": "2", "title": "Article 2", "content": "Content 2"},
        {"id": "3", "title": "Article 3", "content": "Content 3"},
    ]
    
    result = remove_duplicate_posts(posts_no_duplicates)
    print(f"   Input: {len(posts_no_duplicates)} posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 3, Got: {len(result)} ✓" if len(result) == 3 else f"   Expected: 3, Got: {len(result)} ✗")
    
    # Test 2: With string duplicates
    print("\n2. Testing with string ID duplicates:")
    posts_string_duplicates = [
        {"id": "1", "title": "Article 1", "content": "Content 1"},
        {"id": "2", "title": "Article 2", "content": "Content 2"},
        {"id": "1", "title": "Article 1 Duplicate", "content": "Different content"},
        {"id": "3", "title": "Article 3", "content": "Content 3"},
        {"id": "2", "title": "Article 2 Duplicate", "content": "Different content"},
    ]
    
    result = remove_duplicate_posts(posts_string_duplicates)
    print(f"   Input: {len(posts_string_duplicates)} posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 3, Got: {len(result)} ✓" if len(result) == 3 else f"   Expected: 3, Got: {len(result)} ✗")
    
    # Verify the first occurrence is kept
    result_ids = [post["id"] for post in result]
    result_titles = [post["title"] for post in result]
    print(f"   Result IDs: {result_ids}")
    print(f"   Result titles: {result_titles}")
    assert "Article 1" in result_titles and "Article 1 Duplicate" not in result_titles
    print("   ✓ First occurrence kept, duplicates removed")
    
    # Test 3: With UUID duplicates
    print("\n3. Testing with UUID duplicates:")
    uuid1 = UUID("12345678-1234-5678-9012-123456789012")
    uuid2 = UUID("87654321-4321-8765-2109-876543210987")
    
    posts_uuid_duplicates = [
        {"id": uuid1, "title": "Article UUID 1", "content": "Content 1"},
        {"id": uuid2, "title": "Article UUID 2", "content": "Content 2"},
        {"id": uuid1, "title": "Article UUID 1 Duplicate", "content": "Different content"},
        {"id": "3", "title": "Article 3", "content": "Content 3"},
    ]
    
    result = remove_duplicate_posts(posts_uuid_duplicates)
    print(f"   Input: {len(posts_uuid_duplicates)} posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 3, Got: {len(result)} ✓" if len(result) == 3 else f"   Expected: 3, Got: {len(result)} ✗")
    
    # Test 4: Mixed ID types (string and UUID that represent the same value)
    print("\n4. Testing with mixed ID types:")
    uuid_str = "12345678-1234-5678-9012-123456789012"
    uuid_obj = UUID(uuid_str)
    
    posts_mixed_types = [
        {"id": uuid_str, "title": "Article String ID", "content": "Content 1"},
        {"id": uuid_obj, "title": "Article UUID ID", "content": "Content 2"},
        {"id": "different-id", "title": "Article Different", "content": "Content 3"},
    ]
    
    result = remove_duplicate_posts(posts_mixed_types)
    print(f"   Input: {len(posts_mixed_types)} posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 2, Got: {len(result)} ✓" if len(result) == 2 else f"   Expected: 2, Got: {len(result)} ✗")
    
    # Test 5: Empty list
    print("\n5. Testing with empty list:")
    result = remove_duplicate_posts([])
    print(f"   Input: 0 posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 0, Got: {len(result)} ✓" if len(result) == 0 else f"   Expected: 0, Got: {len(result)} ✗")
    
    # Test 6: Posts without ID
    print("\n6. Testing with posts missing ID:")
    posts_missing_id = [
        {"id": "1", "title": "Article 1", "content": "Content 1"},
        {"title": "Article No ID", "content": "Content 2"},  # Missing ID
        {"id": "2", "title": "Article 2", "content": "Content 3"},
    ]
    
    result = remove_duplicate_posts(posts_missing_id)
    print(f"   Input: {len(posts_missing_id)} posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 3, Got: {len(result)} ✓" if len(result) == 3 else f"   Expected: 3, Got: {len(result)} ✗")
    
    # Test 7: All duplicates
    print("\n7. Testing with all duplicates:")
    posts_all_duplicates = [
        {"id": "1", "title": "Article 1", "content": "Content 1"},
        {"id": "1", "title": "Article 1 Dup 1", "content": "Content 2"},
        {"id": "1", "title": "Article 1 Dup 2", "content": "Content 3"},
        {"id": "1", "title": "Article 1 Dup 3", "content": "Content 4"},
    ]
    
    result = remove_duplicate_posts(posts_all_duplicates)
    print(f"   Input: {len(posts_all_duplicates)} posts")
    print(f"   Output: {len(result)} posts")
    print(f"   Expected: 1, Got: {len(result)} ✓" if len(result) == 1 else f"   Expected: 1, Got: {len(result)} ✗")
    print(f"   Kept title: {result[0]['title'] if result else 'None'}")
    
    print("\n" + "="*50)
    print("All tests completed!")


def demonstrate_real_world_scenario():
    """Demonstrate a real-world scenario with candidate posts from different sources."""
    
    print("\nReal-world scenario demonstration:")
    print("="*50)
    
    # Simulate posts from different sources that might have duplicates
    user_ideas = [
        {"id": "idea-1", "title": "User Idea 1", "source": "user_ideas"},
        {"id": "idea-2", "title": "User Idea 2", "source": "user_ideas"},
    ]
    
    latest_idea_bank_posts = [
        {"id": "bank-1", "title": "Bank Article 1", "source": "idea_bank"},
        {"id": "idea-1", "title": "User Idea 1", "source": "idea_bank"},  # Duplicate
        {"id": "bank-2", "title": "Bank Article 2", "source": "idea_bank"},
    ]
    
    new_fetched_articles = [
        {"id": "fetch-1", "title": "Fetched Article 1", "source": "fetched"},
        {"id": "bank-1", "title": "Bank Article 1", "source": "fetched"},  # Duplicate
        {"id": "fetch-2", "title": "Fetched Article 2", "source": "fetched"},
        {"id": "idea-2", "title": "User Idea 2", "source": "fetched"},  # Duplicate
    ]
    
    # Simulate the building of candidate_posts as in main.py
    candidate_posts = []
    candidate_posts.extend(user_ideas)
    candidate_posts.extend(latest_idea_bank_posts)
    candidate_posts.extend(new_fetched_articles)
    
    print(f"Total candidate posts before deduplication: {len(candidate_posts)}")
    print("Posts by source:")
    for post in candidate_posts:
        print(f"  ID: {post['id']}, Title: {post['title']}, Source: {post['source']}")
    
    # Remove duplicates
    unique_posts = remove_duplicate_posts(candidate_posts)
    
    print(f"\nTotal candidate posts after deduplication: {len(unique_posts)}")
    print("Unique posts:")
    for post in unique_posts:
        print(f"  ID: {post['id']}, Title: {post['title']}, Source: {post['source']}")
    
    print(f"\nDuplicates removed: {len(candidate_posts) - len(unique_posts)}")


if __name__ == "__main__":
    test_remove_duplicate_posts()
    demonstrate_real_world_scenario()
