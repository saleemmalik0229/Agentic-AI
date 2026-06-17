import uvicorn
import sys
import logging
from deep_research_backend.api import app
from deep_research_backend.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deep_research_backend")

def main():
    settings = get_settings()
    logger.info("Starting Deep Research Agent Backend...")
    # In production, we'd use Gunicorn or multiple workers
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
