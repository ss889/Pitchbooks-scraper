"""
Combined runner for FastAPI server + Background scheduler.
Runs both the API and the daily scraper in one process.
"""

import logging
import sys
import asyncio
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scheduler and API
from scheduler import get_scheduler
from api import app as fastapi_app

# Global scheduler reference
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Startup: Start the background scheduler
    Shutdown: Stop the scheduler
    """
    global scheduler
    
    # Startup
    logger.info("=" * 60)
    logger.info("Starting PitchBooks Service")
    logger.info("=" * 60)
    
    scheduler = get_scheduler()
    scheduler.start()
    
    logger.info("✓ FastAPI server starting on http://localhost:8000")
    logger.info("✓ API documentation: http://localhost:8000/docs")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down PitchBooks Service")
    logger.info("=" * 60)
    
    if scheduler:
        scheduler.stop()
    logger.info("✓ Service stopped")


# Attach lifespan to FastAPI app
fastapi_app.router.lifespan_context = lifespan


if __name__ == '__main__':
    """
    Run the combined service:
    - FastAPI server on port 8000
    - Background scheduler for daily scraping
    """
    try:
        logger.info("Starting PitchBooks Combined Service...")
        
        # Run uvicorn with FastAPI app
        uvicorn.run(
            fastapi_app,
            host='127.0.0.1',
            port=8000,
            log_level='info',
            reload=False  # Set to True for development with auto-reload
        )
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
