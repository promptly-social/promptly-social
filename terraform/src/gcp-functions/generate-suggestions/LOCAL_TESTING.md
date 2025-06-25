# Local Testing Guide for generate-suggestions Function

This guide explains how to test the `generate_suggestions` Cloud Function locally without deploying to GCP.

## Setup

### 1. Create Environment File

Create a `.env` file in this directory with the following variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here

# OpenRouter API Key for AI generation
OPENROUTER_API_KEY=your-openrouter-api-key-here

# Optional: Number of posts to generate (defaults to 3 if not set)
NUMBER_OF_POSTS_TO_GENERATE=3
```

### 2. Install Dependencies

Make sure you have all required dependencies installed:

```bash
pip install -r requirements.txt
```

## Running the Test

### Basic Test

Run the test script:

```bash
python test_main_local.py
```

The script will:

1. ✅ Check environment variables
2. 🌐 Test CORS preflight handling
3. 👤 Prompt for a user ID (or use default)
4. 🧪 Run the main function with your user ID
5. 🔍 Test error cases

### Test with Specific User ID

When prompted, enter a valid user ID from your Supabase database. The user should have:

- User preferences configured (substacks, topics_of_interest, bio)
- Valid Substack subscriptions in their preferences

### Expected Output

For a successful test, you should see:

- ✅ Environment setup confirmation
- 📊 HTTP status codes (200 for success)
- 📄 Generated post suggestions in JSON format
- 📈 Summary of generated posts

## Test Features

The test script covers:

- ✅ Environment variable validation
- ✅ CORS preflight request handling
- ✅ Valid user ID processing
- ✅ Error handling for missing user_id
- ✅ Error handling for invalid JSON
- ✅ Full function execution with real dependencies

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**

   - Ensure your `.env` file exists and contains all required variables
   - Check that variable names match exactly

2. **Supabase Connection Issues**

   - Verify your Supabase URL and service key are correct
   - Ensure the service key has proper permissions

3. **User Not Found**

   - Make sure the user ID exists in your Supabase database
   - Verify the user has preferences configured

4. **OpenRouter API Issues**
   - Check your OpenRouter API key is valid
   - Ensure you have sufficient credits/quota

### Debug Mode

For more detailed logging, you can modify the logging level in the test script or main function:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with CI/CD

This test script can be integrated into your CI/CD pipeline for automated testing:

```bash
# Set environment variables in CI
export SUPABASE_URL="your-test-url"
export SUPABASE_SERVICE_KEY="your-test-key"
export OPENROUTER_API_KEY="your-test-key"

# Run tests
python test_main_local.py
```

## Next Steps

After successful local testing:

1. Deploy the function to GCP Cloud Functions
2. Test the deployed function via HTTP requests
3. Monitor logs in GCP Console for any issues
