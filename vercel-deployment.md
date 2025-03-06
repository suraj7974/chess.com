# Vercel Deployment Guide for Chess Application

## Environment Variables Setup

1. Go to your Vercel dashboard: https://vercel.com/dashboard
2. Select your chessserver project
3. Click on the "Settings" tab
4. Navigate to "Environment Variables" section
5. Add the following environment variable:
   - **Name**: `GROQ_API_KEY`
   - **Value**: `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`
   - Select all environments (Production, Preview, Development)
6. Click "Save" to apply the changes
7. Redeploy your application

## Verifying Deployment

After setting up the environment variables and redeploying:

1. Visit the debug endpoint: `https://chessserver.vercel.app/api/groq/debug`
2. Check that `api_key_exists` is showing `true`
3. Test the connection with: `https://chessserver.vercel.app/api/groq/test-connection`

## Troubleshooting

If you still see the mock engine being used after setting the environment variable:

1. Check the Vercel build logs for any errors
2. Make sure the `GROQ_API_KEY` environment variable is correctly set
3. Try setting the environment variable directly in the Vercel CLI:

```bash
vercel env add GROQ_API_KEY
```

4. You can also check if the API key is being properly loaded by adding a temporary debug output in your code
