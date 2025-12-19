"""
Main FastAPI application - Simple Search with AI Summary
Uses Exa for search, web scraping + Claude for content summarization
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

from config import settings
from models import (
    SearchRequest,
    SearchResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    HealthCheckResponse,
)
from exa_service import exa_service
from summary_service import summary_service

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Exa FastAPI Backend...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")
    yield
    # Shutdown
    logger.info("Shutting down Exa FastAPI Backend...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI backend for Exa AI search with Claude-powered summaries",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Exception Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "status_code": 500
        }
    )


# ==================== Health Check Endpoint ====================

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check API health and service connectivity
    
    Returns health status, app info, and service connection status
    """
    try:
        exa_connected = await exa_service.health_check()
        anthropic_connected = summary_service.anthropic_client is not None
        
        return HealthCheckResponse(
            status="healthy" if (exa_connected and anthropic_connected) else "degraded",
            app_name=settings.app_name,
            version=settings.app_version,
            exa_api_connected=exa_connected,
            anthropic_api_connected=anthropic_connected,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            app_name=settings.app_name,
            version=settings.app_version,
            exa_api_connected=False,
            anthropic_api_connected=False,
            timestamp=datetime.utcnow().isoformat()
        )


@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint"
)
async def root():
    """Root endpoint - returns API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "search": "/api/v1/search",
            "generate_summary": "/api/v1/generate-summary",
            "health": "/health"
        }
    }


# ==================== Search Endpoint ====================

@app.post(
    "/api/v1/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Search the web using Exa API",
    status_code=status.HTTP_200_OK
)
async def search(request: SearchRequest):
    """
    Search the web using Exa's neural/keyword search
    
    - **query**: Search query string (required)
    - **num_results**: Number of results to return (1-100, default: 10)
    - **search_type**: Type of search - neural, keyword, or auto (default: auto)
    - **include_domains**: List of domains to include in results
    - **exclude_domains**: List of domains to exclude from results
    - **start_published_date**: Filter results published after this date (YYYY-MM-DD)
    - **end_published_date**: Filter results published before this date (YYYY-MM-DD)
    - **category**: Category filter for results
    
    Returns list of search results with titles, URLs, scores, and metadata
    """
    try:
        logger.info(f"Search request: query='{request.query[:50]}...', num_results={request.num_results}")
        
        result = await exa_service.search(
            query=request.query,
            num_results=request.num_results,
            search_type=request.search_type,
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains,
            start_published_date=request.start_published_date,
            end_published_date=request.end_published_date,
            category=request.category,
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# ==================== Generate Summary Endpoint ====================

@app.post(
    "/api/v1/generate-summary",
    response_model=GenerateSummaryResponse,
    tags=["Summary"],
    summary="Generate AI summary for search results",
    status_code=status.HTTP_200_OK
)
async def generate_summary(request: GenerateSummaryRequest):
    """
    Generate comprehensive AI-powered summary from URLs or Exa result IDs
    
    - **urls**: List of URLs to summarize (optional if ids provided)
    - **ids**: List of Exa result IDs (optional if urls provided, but preferred for speed)
    - **query**: Original search query for context (optional)
    - **focus_areas**: What to focus on in the summary (optional)
    
    Priority: Uses IDs if provided (faster with Exa API), falls back to URLs
    
    Uses 3-tier fallback:
    1. Exa summary API (fastest, requires paid plan)
    2. Exa text API + Claude (good quality, requires paid plan)
    3. Web scraping + Claude (works with free tier, slower)
    
    Returns AI-generated summary with key points and source citations
    """
    try:
        logger.info(f"Generate summary request: urls={len(request.urls or [])} ids={len(request.ids or [])}")
        
        # Validate at least one is provided
        if not request.urls and not request.ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'urls' or 'ids' must be provided"
            )
        
        # Limit to 5 items
        if request.urls and len(request.urls) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 URLs per summary request"
            )
        
        if request.ids and len(request.ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 IDs per summary request"
            )
        
        result = await summary_service.generate_summary(
            urls=request.urls,
            ids=request.ids,
            query=request.query,
            focus_areas=request.focus_areas
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate summary failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
