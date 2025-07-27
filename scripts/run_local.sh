#!/bin/bash

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    echo "Please set it using: export OPENAI_API_KEY=your_api_key_here"
    exit 1
else
    echo "OpenAI API key is set (length: ${#OPENAI_API_KEY} characters)"
    echo "API key starts with: ${OPENAI_API_KEY:0:10}..."
fi

# Run the FastAPI server with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 