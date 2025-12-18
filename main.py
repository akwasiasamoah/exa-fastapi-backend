"""
Main FastAPI application
Exa API Backend with search, contents, and similarity endpoints
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from models import (
    SearchRequest,
    SearchResponse,
    ContentsRequest,
    ContentsResponse,
    FindSimilarRequest,
    FindSimilarResponse,
    HealthCheckResponse,
    ErrorResponse,
)
from exa_service import exa_service

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
    description="FastAPI backend for Exa AI search API integration",
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
    Check API health and Exa API connectivity
    
    Returns health status, app info, and Exa API connection status
    """
    try:
        exa_connected = await exa_service.health_check()
        
        return HealthCheckResponse(
            status="healthy" if exa_connected else "degraded",
            app_name=settings.app_name,
            version=settings.app_version,
            exa_api_connected=exa_connected,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            app_name=settings.app_name,
            version=settings.app_version,
            exa_api_connected=False,
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
            "contents": "/api/v1/contents",
            "find_similar": "/api/v1/find-similar",
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


# ==================== Contents Endpoint ====================

@app.post(
    "/api/v1/contents",
    response_model=ContentsResponse,
    tags=["Contents"],
    summary="Get full content for URLs or result IDs",
    status_code=status.HTTP_200_OK
)
async def get_contents(request: ContentsRequest):
    """
    Get full content for specific URLs or Exa result IDs
    
    - **ids**: List of Exa result IDs (from search results)
    - **urls**: List of URLs to fetch content for
    - **text**: Include full text content (default: true)
    - **highlights**: Include relevant highlights (default: false)
    - **summary**: Include AI-generated summary (default: false)
    
    Note: Either ids or urls must be provided (not both)
    
    Returns full content including text, highlights, and summaries as requested
    """
    try:
        # Validate that at least one is provided
        if not request.ids and not request.urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'ids' or 'urls' must be provided"
            )
        
        logger.info(f"Contents request: ids={len(request.ids) if request.ids else 0}, "
                   f"urls={len(request.urls) if request.urls else 0}")
        
        result = await exa_service.get_contents(
            ids=request.ids,
            urls=request.urls,
            text=request.text,
            highlights=request.highlights,
            summary=request.summary,
        )
        
        return ContentsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get contents failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get contents failed: {str(e)}"
        )


# ==================== Find Similar Endpoint ====================

@app.post(
    "/api/v1/find-similar",
    response_model=FindSimilarResponse,
    tags=["Search"],
    summary="Find similar content to a given URL",
    status_code=status.HTTP_200_OK
)
async def find_similar(request: FindSimilarRequest):
    """
    Find content similar to a given URL using Exa's semantic understanding
    
    - **url**: URL to find similar content for (required)
    - **num_results**: Number of similar results to return (1-100, default: 10)
    - **exclude_source_domain**: Exclude results from the same domain (default: false)
    - **category**: Category filter for results
    - **start_published_date**: Filter results published after this date (YYYY-MM-DD)
    - **end_published_date**: Filter results published before this date (YYYY-MM-DD)
    
    Returns list of similar results ranked by semantic similarity
    """
    try:
        logger.info(f"Find similar request: url={request.url}")
        
        result = await exa_service.find_similar(
            url=request.url,
            num_results=request.num_results,
            exclude_source_domain=request.exclude_source_domain,
            category=request.category,
            start_published_date=request.start_published_date,
            end_published_date=request.end_published_date,
        )
        
        return FindSimilarResponse(**result)
        
    except Exception as e:
        logger.error(f"Find similar failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Find similar failed: {str(e)}"
        )


# ==================== Batch Search Endpoint (Bonus) ====================

@app.post(
    "/api/v1/batch-search",
    tags=["Search"],
    summary="Perform multiple searches in a single request",
    status_code=status.HTTP_200_OK
)
async def batch_search(queries: list[str], num_results: int = 10):
    """
    Perform multiple searches in a single request
    
    - **queries**: List of search queries
    - **num_results**: Number of results per query (default: 10)
    
    Returns results for all queries
    """
    try:
        if len(queries) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 queries per batch request"
            )
        
        logger.info(f"Batch search request: {len(queries)} queries")
        
        results = []
        for query in queries:
            try:
                result = await exa_service.search(
                    query=query,
                    num_results=num_results,
                    search_type="auto"
                )
                results.append({
                    "query": query,
                    "status": "success",
                    "data": result
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "status": "error",
                    "error": str(e)
                })
        
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch search failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
