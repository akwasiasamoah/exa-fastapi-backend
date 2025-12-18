"""
Example client for Exa FastAPI Backend
Demonstrates how to use the API from Python applications
"""
import requests
from typing import List, Optional, Dict, Any
import json


class ExaAPIClient:
    """Client for interacting with Exa FastAPI Backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def search(
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
        Perform a search
        
        Args:
            query: Search query
            num_results: Number of results (1-100)
            search_type: Type of search (neural, keyword, auto)
            include_domains: Domains to include
            exclude_domains: Domains to exclude
            start_published_date: Start date (YYYY-MM-DD)
            end_published_date: End date (YYYY-MM-DD)
            category: Category filter
            
        Returns:
            Search results
        """
        payload = {
            "query": query,
            "num_results": num_results,
            "search_type": search_type,
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if start_published_date:
            payload["start_published_date"] = start_published_date
        if end_published_date:
            payload["end_published_date"] = end_published_date
        if category:
            payload["category"] = category
        
        response = self.session.post(
            f"{self.base_url}/api/v1/search",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_contents(
        self,
        ids: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
        text: bool = True,
        highlights: bool = False,
        summary: bool = False,
    ) -> Dict[str, Any]:
        """
        Get content for URLs or IDs
        
        Args:
            ids: List of result IDs
            urls: List of URLs
            text: Include full text
            highlights: Include highlights
            summary: Include summary
            
        Returns:
            Content results
        """
        payload = {
            "text": text,
            "highlights": highlights,
            "summary": summary,
        }
        
        if ids:
            payload["ids"] = ids
        if urls:
            payload["urls"] = urls
        
        response = self.session.post(
            f"{self.base_url}/api/v1/contents",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def find_similar(
        self,
        url: str,
        num_results: int = 10,
        exclude_source_domain: bool = False,
        category: Optional[str] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find similar content
        
        Args:
            url: URL to find similar content for
            num_results: Number of results
            exclude_source_domain: Exclude same domain
            category: Category filter
            start_published_date: Start date
            end_published_date: End date
            
        Returns:
            Similar results
        """
        payload = {
            "url": url,
            "num_results": num_results,
            "exclude_source_domain": exclude_source_domain,
        }
        
        if category:
            payload["category"] = category
        if start_published_date:
            payload["start_published_date"] = start_published_date
        if end_published_date:
            payload["end_published_date"] = end_published_date
        
        response = self.session.post(
            f"{self.base_url}/api/v1/find-similar",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def batch_search(
        self,
        queries: List[str],
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform batch search
        
        Args:
            queries: List of queries (max 10)
            num_results: Results per query
            
        Returns:
            Batch results
        """
        payload = {
            "queries": queries,
            "num_results": num_results
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/batch-search",
            json=payload
        )
        response.raise_for_status()
        return response.json()


# ==================== Example Usage ====================

def example_basic_search():
    """Example: Basic search"""
    print("\n" + "="*60)
    print("Example 1: Basic Search")
    print("="*60)
    
    client = ExaAPIClient()
    
    # Perform search
    results = client.search(
        query="Python FastAPI tutorials",
        num_results=5
    )
    
    print(f"\nFound {len(results['results'])} results:")
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Score: {result.get('score', 'N/A')}")


def example_filtered_search():
    """Example: Search with filters"""
    print("\n" + "="*60)
    print("Example 2: Filtered Search")
    print("="*60)
    
    client = ExaAPIClient()
    
    results = client.search(
        query="machine learning research",
        num_results=5,
        search_type="neural",
        include_domains=["arxiv.org", "nature.com"],
        start_published_date="2025-01-01"
    )
    
    print(f"\nFound {len(results['results'])} research papers:")
    for result in results['results']:
        print(f"- {result['title']}")


def example_get_content():
    """Example: Get full content"""
    print("\n" + "="*60)
    print("Example 3: Get Content")
    print("="*60)
    
    client = ExaAPIClient()
    
    # Get content for specific URLs
    contents = client.get_contents(
        urls=["https://fastapi.tiangolo.com/"],
        text=True,
        highlights=True
    )
    
    for content in contents['results']:
        print(f"\nTitle: {content['title']}")
        print(f"URL: {content['url']}")
        print(f"Text length: {len(content.get('text', ''))} characters")
        if content.get('highlights'):
            print(f"Highlights: {len(content['highlights'])} found")


def example_find_similar():
    """Example: Find similar content"""
    print("\n" + "="*60)
    print("Example 4: Find Similar")
    print("="*60)
    
    client = ExaAPIClient()
    
    similar = client.find_similar(
        url="https://fastapi.tiangolo.com/",
        num_results=5,
        exclude_source_domain=True
    )
    
    print(f"\nFound {len(similar['results'])} similar articles:")
    for result in similar['results']:
        print(f"- {result['title']}")
        print(f"  {result['url']}")


def example_batch_search():
    """Example: Batch search"""
    print("\n" + "="*60)
    print("Example 5: Batch Search")
    print("="*60)
    
    client = ExaAPIClient()
    
    results = client.batch_search(
        queries=[
            "Python web development",
            "FastAPI performance",
            "API best practices"
        ],
        num_results=3
    )
    
    for item in results['results']:
        query = item['query']
        status = item['status']
        print(f"\nQuery: {query}")
        print(f"Status: {status}")
        
        if status == 'success':
            data = item['data']
            print(f"Results: {len(data['results'])}")


def example_workflow():
    """Example: Complete workflow"""
    print("\n" + "="*60)
    print("Example 6: Complete Workflow")
    print("="*60)
    
    client = ExaAPIClient()
    
    # 1. Check health
    health = client.health_check()
    print(f"API Status: {health['status']}")
    
    # 2. Search for content
    print("\n1. Searching for AI articles...")
    search_results = client.search(
        query="artificial intelligence breakthroughs",
        num_results=3,
        search_type="neural"
    )
    
    # 3. Get full content for top result
    if search_results['results']:
        top_result = search_results['results'][0]
        print(f"\n2. Getting content for: {top_result['title']}")
        
        content = client.get_contents(
            urls=[top_result['url']],
            text=True,
            summary=True
        )
        
        # 4. Find similar content
        print(f"\n3. Finding similar content...")
        similar = client.find_similar(
            url=top_result['url'],
            num_results=3
        )
        
        print(f"\nFound {len(similar['results'])} similar articles")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXA FASTAPI BACKEND - PYTHON CLIENT EXAMPLES")
    print("="*60)
    
    try:
        # Run examples
        example_basic_search()
        example_filtered_search()
        example_get_content()
        example_find_similar()
        example_batch_search()
        example_workflow()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
