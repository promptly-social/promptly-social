# Social Media Analysis - GCP Cloud Function

This directory contains a Python-based GCP Cloud Function that analyzes social media content for writing style, topics, and engagement patterns. Currently supports Substack and LinkedIn platforms.

## 🏗️ Architecture

```
Backend FastAPI ----HTTP----> GCP Cloud Function ----Updates----> Supabase Database
     ↓                              ↓                                    ↓
1. User triggers analysis    2. Fetches platform content        3. Stores analysis results
2. Sets analysis_started_at  3. Performs NLP analysis           4. Sets analysis_completed_at
3. Calls GCP function        4. Analyzes writing patterns       5. Updates writing_style_analysis

Supported Platforms:
- Substack: RSS feed + API analysis
- LinkedIn: Unipile API integration
```

## 📁 Files

- `main.py` - Main Cloud Function code
- `substack_analyzer.py` - Substack content analysis module
- `linkedin_analyzer.py` - LinkedIn content analysis module (via Unipile)
- `requirements.txt` - Python dependencies
- `env.example` - Environment variables template
- `test_analyzer_local.py` - Substack analyzer local test script
- `test_linkedin_analyzer_local.py` - LinkedIn analyzer local test script
- `README.md` - This file

## 🚀 Deployment

### Prerequisites

1. **Install gcloud CLI**:

   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with GCP**:

   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable required APIs** (done automatically by deploy script):
   - Cloud Functions API
   - Cloud Build API
   - Cloud Logging API

### Deploy the Function

1. **Navigate to the function directory**:

   ```bash
   cd gcp-functions/analyze-substack
   ```

2. **Run the deployment script**:

   ```bash
   ./deploy.sh YOUR_GCP_PROJECT_ID us-central1
   ```

3. **Set environment variables**:
   ```bash
   gcloud functions deploy analyze-substack \
     --update-env-vars SUPABASE_URL=your_supabase_url,SUPABASE_SERVICE_ROLE_KEY=your_service_key \
     --region=us-central1
   ```

### Manual Deployment (Alternative)

```bash
gcloud functions deploy analyze-substack \
  --gen2 \
  --runtime=python313 \
  --region=us-central1 \
  --source=. \
  --entry-point=analyze_substack \
  --memory=512MB \
  --timeout=540s \
  --trigger=http \
  --allow-unauthenticated \
  --set-env-vars="SUPABASE_URL=your_url,SUPABASE_SERVICE_ROLE_KEY=your_key"
```

## ⚙️ Configuration

### Environment Variables

Set these in the GCP Console or via gcloud:

| Variable                        | Description                                 | Required |
| ------------------------------- | ------------------------------------------- | -------- |
| `SUPABASE_URL`                  | Your Supabase project URL                   | Yes      |
| `SUPABASE_SERVICE_ROLE_KEY`     | Supabase service role key                   | Yes      |
| `OPENROUTER_API_KEY`            | OpenRouter API key for LLM analysis         | Yes      |
| `UNIPILE_DSN`                   | Unipile DSN hostname for LinkedIn           | Yes      |
| `UNIPILE_ACCESS_TOKEN`          | Unipile access token for LinkedIn           | Yes      |
| `MAX_POSTS_TO_ANALYZE`          | Max Substack posts to analyze (default: 10) | No       |
| `MAX_POSTS_TO_ANALYZE_LINKEDIN` | Max LinkedIn posts to analyze (default: 20) | No       |

### Backend Configuration

Update your backend's environment variables:

```bash
# Add to backend/.env or deployment config
GCP_ANALYSIS_FUNCTION_URL=https://us-central1-your-project.cloudfunctions.net/analyze-substack
```

## 🔧 Development

### Local Testing

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:

   ```bash
   export SUPABASE_URL="your_supabase_url"
   export SUPABASE_SERVICE_ROLE_KEY="your_service_key"
   ```

3. **Run locally**:

   ```bash
   functions-framework --target=analyze_substack --debug
   ```

4. **Test the function**:

   **Substack analysis:**

   ```bash
   curl -X POST http://localhost:8080 \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-uuid", "platform": "substack", "platform_username": "testuser", "content_to_analyze": ["bio", "writing_style"]}'
   ```

   **LinkedIn analysis:**

   ```bash
   curl -X POST http://localhost:8080 \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-uuid", "platform": "linkedin", "platform_username": "unipile-account-id", "content_to_analyze": ["bio", "writing_style"]}'
   ```

5. **Test analyzers directly**:

   ```bash
   # Test Substack analyzer
   python test_analyzer_local.py stratechery

   # Test LinkedIn analyzer
   python test_linkedin_analyzer_local.py your-unipile-account-id
   ```

### Function Logs

View logs in real-time:

```bash
gcloud functions logs tail analyze-substack --region=us-central1
```

## 📊 How It Works

1. **Trigger**: Backend calls the function when user requests analysis
2. **Validation**: Function validates user and connection exist
3. **Analysis**:
   - **Substack**: Fetches RSS feed, parses recent posts
   - **LinkedIn**: Fetches posts via Unipile API
   - Analyzes writing style using NLP (OpenRouter/OpenAI)
   - Extracts topics and content patterns
4. **Storage**: Updates Supabase with results and completion timestamp

## 🔍 Analysis Features

The function analyzes:

- **Writing Style**: Tone, complexity, sentence structure
- **Topics**: Extracted themes and categories
- **Posting Patterns**: Frequency, optimal times
- **Engagement**: Subscriber estimates, performance metrics
- **Content Categories**: Educational, opinion, news analysis

## 🛡️ Security

- Function requires valid Supabase connection
- Validates analysis was properly initiated
- CORS enabled for web requests
- Service role key for database access
- Unauthenticated access (protected by validation logic)

## 📈 Monitoring

Monitor the function via:

- **GCP Console**: Cloud Functions dashboard
- **Logs**: `gcloud functions logs tail analyze-substack`
- **Metrics**: Function execution time, error rates
- **Supabase**: Database updates and analysis results

## 🔄 Updating

To update the function:

1. Make changes to `main.py`
2. Run deployment script again: `./deploy.sh`
3. Check logs for successful deployment

## 🎯 Next Steps

1. **Implement Real Analysis**: Replace placeholder logic in `fetch_substack_content()`
2. **Add Rate Limiting**: Implement rate limiting for API calls
3. **Error Handling**: Add more sophisticated error handling
4. **Caching**: Cache analysis results to avoid re-processing
5. **Monitoring**: Set up alerts for function failures
