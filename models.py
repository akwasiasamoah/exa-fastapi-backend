"""
Pydantic models for request validation and response serialization
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime


# ==================== Search Models ====================

class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    search_type: Literal["neural", "keyword", "auto"] = Field(default="auto", description="Type of search")
    include_domains: Optional[List[str]] = Field(default=None, description="Domains to include")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Domains to exclude")
    start_published_date: Optional[str] = Field(default=None, description="Start date filter (YYYY-MM-DD)")
    end_published_date: Optional[str] = Field(default=None, description="End date filter (YYYY-MM-DD)")
    category: Optional[str] = Field(default=None, description="Category filter")
    
    @field_validator('start_published_date', 'end_published_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class SearchResult(BaseModel):
    """Individual search result"""
    title: Optional[str] = None
    url: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    score: Optional[float] = None
    id: str
    text: Optional[str] = None
    highlights: Optional[List[str]] = None
    highlight_scores: Optional[List[float]] = None


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    results: List[SearchResult]
    autoprompt_string: Optional[str] = None
    request_id: Optional[str] = None


# ==================== Contents Models ====================

class ContentsRequest(BaseModel):
    """Request model for contents endpoint"""
    ids: Optional[List[str]] = Field(default=None, description="List of result IDs")
    urls: Optional[List[str]] = Field(default=None, description="List of URLs")
    text: bool = Field(default=True, description="Include full text content")
    highlights: bool = Field(default=False, description="Include highlights")
    summary: bool = Field(default=False, description="Include AI summary")
    
    @field_validator('ids', 'urls')
    @classmethod
    def validate_at_least_one(cls, v, info):
        # Check if at least one of ids or urls is provided
        if v is None and info.data.get('ids') is None and info.data.get('urls') is None:
            raise ValueError('Either ids or urls must be provided')
        return v


class ContentResult(BaseModel):
    """Individual content result"""
    id: str
    url: str
    title: Optional[str] = None
    text: Optional[str] = None
    highlights: Optional[List[str]] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None


class ContentsResponse(BaseModel):
    """Response model for contents endpoint"""
    results: List[ContentResult]
    request_id: Optional[str] = None


# ==================== Find Similar Models ====================

class FindSimilarRequest(BaseModel):
    """Request model for find similar endpoint"""
    url: str = Field(..., description="URL to find similar content for")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results")
    exclude_source_domain: bool = Field(default=False, description="Exclude results from same domain")
    category: Optional[str] = Field(default=None, description="Category filter")
    start_published_date: Optional[str] = Field(default=None, description="Start date filter")
    end_published_date: Optional[str] = Field(default=None, description="End date filter")


class FindSimilarResponse(BaseModel):
    """Response model for find similar endpoint"""
    results: List[SearchResult]
    request_id: Optional[str] = None


# ==================== Health Check Models ====================

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    app_name: str
    version: str
    exa_api_connected: bool
    timestamp: str


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
