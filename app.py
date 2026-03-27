from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from slowapi import SlowAPI, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.analysis.scanner import Scanner
from src.config.universe import TICKERS_ALL
from pathlib import Path
import uvicorn
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = SlowAPI(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Use centralized ticker list
TICKERS = TICKERS_ALL

# Global store for results
state = {"signals": []}

# Base directory for static files
BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / 'index.html'


@app.on_event("startup")
async def startup_event():
    """Initialize scanner and load signals on startup."""
    logger.info(f"Starting scanner for {len(TICKERS)} tickers...")
    try:
        scanner = Scanner(TICKERS)
        results = scanner.scan()
        state["signals"] = results.to_dict(orient="records")
        logger.info(f"Loaded {len(state['signals'])} signals")
    except Exception as e:
        logger.error(f"Error during startup scan: {e}")
        state["signals"] = []


@app.get("/")
async def read_index(request: Request):
    """Serve the index.html file."""
    if not INDEX_PATH.exists():
        logger.error(f"Index file not found at {INDEX_PATH}")
        raise HTTPException(status_code=404, detail="Index file not found")
    return FileResponse(str(INDEX_PATH))


@app.get("/signals")
@limiter.limit("10/minute")
async def get_signals(request: Request):
    """
    Get current trading signals.
    Rate limited to 10 requests per minute.
    """
    return {"signals": state["signals"], "count": len(state["signals"])}


@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "healthy", "signals_count": len(state["signals"])}


if __name__ == "__main__":
    logger.info("Starting FastAPI server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
