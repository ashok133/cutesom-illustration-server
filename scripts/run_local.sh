#!/bin/bash

# Check connectivity or just print statusecho "Checking environment configuration..."

# Default bucket for local dev
export FIREBASE_STORAGE_BUCKET="cutesom-storybooks"

# Check for keys (just warning if likely needed)
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY is not set (required for 'gpt-image')"
fi
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Warning: GEMINI_API_KEY is not set (required for 'nano-banana')"
fi

# Run the FastAPI server with uvicorn
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 