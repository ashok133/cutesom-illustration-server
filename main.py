"""Cloud Function entry point for the Cutesom Illustration Server."""
import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.endpoints import router as api_router

# Initialize FastAPI application
app = FastAPI(
    title="Cutesom Illustration Server",
    description="API for generating and managing storybook illustrations",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Dict[str, str]: Status response
    """
    return {"status": "healthy"}
