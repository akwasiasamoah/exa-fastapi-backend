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


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    results: List[SearchResult]
    autoprompt_string: Optional[str] = None
    request_id: Optional[str] = None


# ==================== Summary Models ====================

class GenerateSummaryRequest(BaseModel):
    """Request model for generate summary endpoint"""
    urls: List[str] = Field(..., min_items=1, max_items=5, description="URLs to summarize (max 5)")
    query: Optional[str] = Field(default=None, description="Original search query for context")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Areas to focus on (e.g., 'key findings', 'statistics', 'conclusions')"
    )


class SourceInfo(BaseModel):
    """Information about a source used in the summary"""
    url: str
    title: Optional[str] = None
    scraped_successfully: bool = True


class GenerateSummaryResponse(BaseModel):
    """Response model for generate summary endpoint"""
    summary: str = Field(..., description="AI-generated comprehensive summary")
    key_points: List[str] = Field(default=[], description="Key points extracted from sources")
    sources: List[SourceInfo] = Field(default=[], description="Sources used in the summary")
    query_context: Optional[str] = Field(default=None, description="Original query for context")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    generated_by: str = "claude-sonnet-4"


# ==================== Health Check Models ====================

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    app_name: str
    version: str
    exa_api_connected: bool
    anthropic_api_connected: bool = False
    timestamp: str
