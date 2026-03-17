"""
Main FastAPI application for Anime CDN.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import init_db
from api.routes import series, episodes, users, auth
import config

# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="Anime CDN API",
    description="REST API for anime content delivery network",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount HLS video files as static files
# This serves the processed videos at /hls/{video_file_id}/...
if os.path.exists(config.OUTPUT_DIR):
    app.mount("/hls", StaticFiles(directory=config.OUTPUT_DIR), name="hls")

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(series.router, prefix="/api")
app.include_router(episodes.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Anime CDN API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "series": "/api/series",
            "episodes": "/api/episodes",
            "users": "/api/users"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes during development
    )
