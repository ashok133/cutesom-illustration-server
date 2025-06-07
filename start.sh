#!/bin/bash

# Print environment variables for debugging
echo "Environment variables:"
env

# Get the port from environment variable or default to 8080
PORT=${PORT:-8080}
echo "Using port: $PORT"

# Start the FastAPI application with debug logging
exec uvicorn main:app --host 0.0.0.0 --port $PORT --log-level debug 