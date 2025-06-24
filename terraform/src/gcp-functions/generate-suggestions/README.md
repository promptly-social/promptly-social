# Generate Suggestions Cloud Function

This Google Cloud Function generates content suggestions for users by fetching their latest Substack posts based on their preferences.

## Purpose

The function:

1. Takes a user's user_id as input
2. Queries Supabase for user preferences (topics, websites, substacks, bio)
3. Fetches the latest posts from subscribed Substack newsletters (last 3 days)
4. Processes multiple newsletters in parallel for better performance
5. Returns a list of recent posts with metadata

## API

### Endpoint

- **Method**: POST
- **Content-Type**: application/json

### Request Body

```json
{
  "user_id": "uuid-string"
}
```

### Response

```json
{
  "success": true,
  "user_preferences": {
    "topics_of_interest": ["topic1", "topic2"],
    "websites": ["https://example.com"],
    "substacks": ["https://newsletter.substack.com"],
    "bio": "User bio text"
  },
  "latest_posts": [
    {
      "url": "https://newsletter.substack.com/p/post-title",
      "title": "Post Title",
      "subtitle": "Post Subtitle",
      "author": "Author Name",
      "post_date": "2023-12-01T10:00:00Z",
      "newsletter_url": "https://newsletter.substack.com",
      "newsletter_name": "Newsletter Name",
      "content_preview": "First 500 characters of content..."
    }
  ],
  "total_posts": 10,
  "total_newsletters": 3,
  "message": "Found 10 recent posts from 3 newsletters"
}
```

## Environment Variables

Required environment variables:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `NUMBER_OF_POSTS_TO_GENERATE`: Number of posts to generate for the run (default: 5)

## Features

- **Parallel Processing**: Fetches posts from multiple newsletters simultaneously
- **Date Filtering**: Only returns posts from the last 3 days
- **Robust Error Handling**: Continues processing even if some newsletters fail
- **Metadata Extraction**: Includes rich metadata for each post
- **CORS Support**: Handles preflight requests

## Dependencies

- `functions-framework`: Google Cloud Functions framework
- `supabase`: Supabase Python client
- `substack-api`: Substack API client
- `httpx`: HTTP client
- `requests`: HTTP library

## Usage Example

```python
import requests

response = requests.post(
    'https://your-function-url',
    json={'user_id': 'user-uuid-here'}
)

data = response.json()
if data['success']:
    posts = data['latest_posts']
    print(f"Found {len(posts)} recent posts")
```

## Error Handling

The function includes comprehensive error handling:

- Invalid JSON requests return 400 status
- Missing user_id returns 400 status
- Supabase connection errors return 500 status
- Individual newsletter failures are logged but don't stop processing
- Date parsing errors are handled gracefully

## Performance Considerations

- Uses ThreadPoolExecutor for parallel processing
- Limits concurrent requests to prevent rate limiting
- Includes 30-second timeout per newsletter
- Limits content preview to 500 characters
- Sorts results by date (newest first)
