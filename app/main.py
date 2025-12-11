"""
ANCA FastAPI Application (Refactored)
Proper file structure with separation of concerns
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.schemas.models import HealthResponse
from app.api.routers import generation, articles

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

# Import custom formatter and session utility
from app.core.logging_utils import AnsiStrippingFormatter, get_session_log_file

# Get session log file
log_file = get_session_log_file("anca", settings.logs_dir)

file_formatter = AnsiStrippingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File Handler (Session-based)
file_handler = logging.FileHandler(
    str(log_file),
    encoding='utf-8'
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(settings.log_level)

# Console Handler (Keep for debugging)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(settings.log_level)

# Setup Root Logger - explicitly add handlers instead of using basicConfig
# This ensures handlers are added even if logging was already initialized
root_logger = logging.getLogger()
root_logger.setLevel(settings.log_level)

# Clear any existing handlers to avoid duplicates
root_logger.handlers.clear()

# Add our handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Redirect stdout to logger to capture CrewAI output
from app.core.logging_utils import StreamToLogger
import sys
sys.stdout = StreamToLogger(root_logger, logging.INFO)


logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generation.router)
app.include_router(articles.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting ANCA API")
    settings.articles_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    # Verify Ollama connectivity
    import requests
    try:
        logger.info(f"Checking Ollama connectivity at {settings.ollama_base_url}")
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            model_names = [m['name'] for m in models.get('models', [])]
            logger.info(f"✓ Ollama connected successfully. Available models: {model_names}")

            # Verify required models
            required_models = ['llama3.1:8b', 'mistral:7b']
            missing_models = [m for m in required_models if m not in model_names]
            if missing_models:
                logger.error(f"✗ Missing required models: {missing_models}")
                logger.error("Please run the model-puller service to download required models")
            else:
                logger.info(f"✓ All required models are available")
        else:
            logger.error(f"✗ Ollama API returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Failed to connect to Ollama at {settings.ollama_base_url}: {e}")
        logger.error("The API will start but jobs may fail. Please check Ollama service.")


@app.get("/", tags=["Root"])
def read_root():
    """API root endpoint"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    articles_count = len(list(settings.articles_dir.glob("*.md"))) if settings.articles_dir.exists() else 0
    
    return HealthResponse(
        status="healthy",
        ollama_url=settings.ollama_base_url,
        articles_dir=str(settings.articles_dir),
        articles_count=articles_count
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
