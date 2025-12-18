"""
Exa service layer - handles all interactions with Exa API
"""
from exa_py import Exa
from typing import List, Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class ExaService:
    """Service class for Exa API operations"""
    
    def __init__(self):
        """Initialize Exa client with API key"""
        self.client = Exa(api_key=settings.exa_api_key)
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "auto",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform search using Exa API
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-100)
            search_type: Type of search (neural, keyword, auto)
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            start_published_date: Filter results after this date
            end_published_date: Filter results before this date
            category: Category filter
            
        Returns:
            Dictionary containing search results
        """
        try:
            logger.info(f"Executing search: query='{query}', num_results={num_results}, type={search_type}")
            
            # Build search parameters
            search_params = {
                "query": query,
                "num_results": num_results,
                "type": search_type,
            }
            
            # Add optional parameters
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            if start_published_date:
                search_params["start_published_date"] = start_published_date
            if end_published_date:
                search_params["end_published_date"] = end_published_date
            if category:
                search_params["category"] = category
            
            # Execute search
            response = self.client.search(**search_params)
            
            # Convert to dictionary
            result = {
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "published_date": r.published_date,
                        "author": r.author,
                        "score": r.score,
                        "id": r.id,
                    }
                    for r in response.results
                ],
                "autoprompt_string": getattr(response, 'autoprompt_string', None),
                "request_id": getattr(response, 'request_id', None)
            }
            
            logger.info(f"Search completed successfully: {len(result['results'])} results")
            return result
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def get_contents(
        self,
        ids: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
        text: bool = True,
        highlights: bool = False,
        summary: bool = False,
    ) -> Dict[str, Any]:
        """
        Get contents for URLs or IDs
        
        Args:
            ids: List of Exa result IDs
            urls: List of URLs
            text: Include full text content
            highlights: Include highlights
            summary: Include AI-generated summary
            
        Returns:
            Dictionary containing content results
        """
        try:
            logger.info(f"Fetching contents: ids={len(ids) if ids else 0}, urls={len(urls) if urls else 0}")
            
            # Build content retrieval parameters
            content_params = {}
            if text:
                content_params["text"] = True
            if highlights:
                content_params["highlights"] = True
            if summary:
                content_params["summary"] = True
            
            # Use IDs or URLs
            if ids:
                response = self.client.get_contents(ids=ids, **content_params)
            elif urls:
                response = self.client.get_contents(urls=urls, **content_params)
            else:
                raise ValueError("Either ids or urls must be provided")
            
            # Convert to dictionary
            result = {
                "results": [
                    {
                        "id": r.id,
                        "url": r.url,
                        "title": r.title,
                        "text": getattr(r, 'text', None) if text else None,
                        "highlights": getattr(r, 'highlights', None) if highlights else None,
                        "summary": getattr(r, 'summary', None) if summary else None,
                        "author": r.author,
                        "published_date": r.published_date,
                    }
                    for r in response.results
                ],
                "request_id": getattr(response, 'request_id', None)
            }
            
            logger.info(f"Contents fetched successfully: {len(result['results'])} items")
            return result
            
        except Exception as e:
            logger.error(f"Get contents failed: {str(e)}")
            raise
    
    async def find_similar(
        self,
        url: str,
        num_results: int = 10,
        exclude_source_domain: bool = False,
        category: Optional[str] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find similar content to a given URL
        
        Args:
            url: URL to find similar content for
            num_results: Number of results to return
            exclude_source_domain: Exclude results from same domain
            category: Category filter
            start_published_date: Filter results after this date
            end_published_date: Filter results before this date
            
        Returns:
            Dictionary containing similar results
        """
        try:
            logger.info(f"Finding similar content for: {url}")
            
            # Build parameters
            params = {
                "url": url,
                "num_results": num_results,
                "exclude_source_domain": exclude_source_domain,
            }
            
            if category:
                params["category"] = category
            if start_published_date:
                params["start_published_date"] = start_published_date
            if end_published_date:
                params["end_published_date"] = end_published_date
            
            # Execute find similar
            response = self.client.find_similar(**params)
            
            # Convert to dictionary
            result = {
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "published_date": r.published_date,
                        "author": r.author,
                        "score": r.score,
                        "id": r.id,
                    }
                    for r in response.results
                ],
                "request_id": getattr(response, 'request_id', None)
            }
            
            logger.info(f"Find similar completed: {len(result['results'])} results")
            return result
            
        except Exception as e:
            logger.error(f"Find similar failed: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Exa API is accessible
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Simple test search to verify connection
            response = self.client.search(query="test", num_results=1)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


# Singleton instance
exa_service = ExaService()
