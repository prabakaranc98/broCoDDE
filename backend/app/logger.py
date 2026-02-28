"""
BroCoDDE — Structured Logger & Observability
Provides a centralized logger and a FastAPI middleware for request tracing.
"""

import logging
import sys
import time
from typing import Callable

from fastapi import Request, Response

# ── Logger Setup ──────────────────────────────────────────────────────────────

logger = logging.getLogger("brocodde")
logger.setLevel(logging.INFO)

# Use a clean, structured format for the console
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


# ── Middleware ────────────────────────────────────────────────────────────────

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Trace all HTTP requests with timing and status codes."""
    start_time = time.perf_counter()
    
    # Log request start for mutating endpoints
    if request.method != "GET" and request.method != "OPTIONS":
        logger.info(f"→ {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        
        # Log response status and timing
        status_category = response.status_code // 100
        level = logging.ERROR if status_category == 5 else (logging.WARNING if status_category == 4 else logging.INFO)
        
        if request.method != "OPTIONS":  # Skip noisy preflight logs
            logger.log(
                level,
                f"← {response.status_code} {request.method} {request.url.path} ({process_time * 1000:.1f}ms)"
            )
            
        return response

    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.exception(f"🧨 500 {request.method} {request.url.path} ({process_time * 1000:.1f}ms) — {str(e)}")
        raise
