from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import logging
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Thai PDF OCR API",
    description="Extract Thai text from PDF files using text extraction and OCR fallback, "
                "then structure into JSON using LLM",
    version="2.0.0",
)

# CORS configuration - customize for production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Thai PDF OCR API",
        "version": "2.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    import os
    return {
        "status": "healthy",
        "version": "2.0.0",
        "checks": {
            "api": "ok",
            "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY"))
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
