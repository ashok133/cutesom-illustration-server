# Cutesum Illustration Server

A FastAPI-based service for generating and managing storybook illustrations using OpenAI's image generation API.

## Features

- Parallel processing of multiple illustrations
- Firebase Storage integration
- Job management system
- Error handling and retry logic
- Secure API endpoints
- Monitoring and logging

## Project Structure

```
.
├── config/             # Configuration files (prompts, etc.)
├── schemas/            # Data models and request/response schemas
├── services/           # Business logic (OpenAI, Firebase services)
├── scripts/            # Utility scripts (deployment, initialization)
├── tests/              # Test files
├── main.py            # Application entry point
├── requirements.txt    # Project dependencies
└── Dockerfile         # Container configuration
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   FIREBASE_CREDENTIALS=your_firebase_credentials
   FIREBASE_STORAGE_BUCKET=your_bucket_name
   ```

4. Run the server:
   ```bash
   # For local development
   ./scripts/run_local.sh
   
   # Or directly with uvicorn
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Development

- Format code:
  ```bash
  black .
  ```

- Lint code:
  ```bash
  flake8
  ```

- Run tests:
  ```bash
  pytest
  ```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `FIREBASE_CREDENTIALS`: Firebase service account credentials
- `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket name
- `MAX_CONCURRENT_JOBS`: Maximum number of concurrent generation jobs
- `JOB_TIMEOUT`: Maximum time for job completion (seconds)
- `RETRY_ATTEMPTS`: Number of retry attempts for failed generations
- `RATE_LIMIT`: Maximum requests per minute

## License

MIT 