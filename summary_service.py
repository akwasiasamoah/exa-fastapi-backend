"""
Summary service - handles AI-powered summarization
Priority: Exa API → Fallback to web scraping + Claude
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from config import settings
import logging
import anthropic
from models import GenerateSummaryResponse, SourceInfo
import urllib3

# Suppress SSL warnings for sites with cert issues (last resort fallback)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SummaryService:
    """Service class for AI-powered summarization"""
    
    def __init__(self):
        """Initialize Exa and Claude clients if API keys are available"""
        from exa_py import Exa
        
        self.exa_client = None
        if settings.exa_api_key:
            try:
                self.exa_client = Exa(api_key=settings.exa_api_key)
                logger.info("Exa client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Exa client: {e}")
        
        self.anthropic_client = None
        if settings.anthropic_api_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    async def generate_summary(
        self,
        urls: Optional[List[str]] = None,
        ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        focus_areas: Optional[List[str]] = None
    ) -> GenerateSummaryResponse:
        """
        Generate AI summary from URLs or Exa result IDs
        
        Strategy:
        1. Try Exa API with IDs (if provided) - fastest
        2. Try Exa API with URLs (if no IDs) - still fast
        3. Fallback to web scraping + Claude
        
        Args:
            urls: List of URLs to summarize
            ids: List of Exa result IDs (preferred if available)
            query: Original search query for context
            focus_areas: What to focus on in the summary
            
        Returns:
            GenerateSummaryResponse with AI summary and sources
        """
        if not self.anthropic_client:
            raise Exception("Anthropic API key not configured. Please set ANTHROPIC_API_KEY in .env")
        
        # Determine what to use
        use_ids = ids and len(ids) > 0
        use_urls = urls and len(urls) > 0
        
        if not use_ids and not use_urls:
            raise Exception("Either urls or ids must be provided")
        
        # Limit to 5 items
        items = (ids[:5] if use_ids else urls[:5])
        items_type = "IDs" if use_ids else "URLs"
        
        logger.info(f"🚀 Generating summary for {len(items)} {items_type}")
        
        # Try Strategy 1 & 2: Exa API (with IDs or URLs)
        if self.exa_client:
            logger.info(f"📡 Trying Exa API with {items_type}...")
            
            # Try summary first
            try:
                result = await self._try_exa_with_summary(items, use_ids, query, focus_areas)
                logger.info("✅ Success with Exa summary API!")
                return result
            except Exception as e:
                logger.warning(f"⚠️  Exa summary failed: {e}")
                logger.info("🔄 Falling back to Exa text + Claude...")
                
                # Try text
                try:
                    result = await self._try_exa_with_text(items, use_ids, query, focus_areas)
                    logger.info("✅ Success with Exa text + Claude!")
                    return result
                except Exception as e:
                    logger.warning(f"⚠️  Exa text also failed: {e}")
                    logger.info("🔄 Falling back to web scraping + Claude...")
        
        # Strategy 3: Web scraping + Claude (last resort)
        # Need URLs for scraping
        if not use_urls:
            raise Exception("Exa API failed and no URLs provided for web scraping fallback")
        
        logger.info("🕷️  Using web scraping + Claude...")
        result = await self._try_web_scraping(urls[:5], query, focus_areas)
        logger.info("✅ Success with web scraping + Claude!")
        return result
    
    async def _try_exa_with_summary(
        self,
        items: List[str],
        use_ids: bool,
        query: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> GenerateSummaryResponse:
        """
        Try using Exa's summary API directly
        
        This is the fastest and cleanest option but requires paid plan
        """
        # Build summary query
        summary_query = self._build_summary_query_for_exa(query, focus_areas)
        
        # Build request body - use ids or urls
        request_body = {
            "summary": {"query": summary_query}
        }
        
        if use_ids:
            request_body["ids"] = items
            logger.info(f"Calling Exa summary API with {len(items)} IDs...")
        else:
            request_body["urls"] = items
            logger.info(f"Calling Exa summary API with {len(items)} URLs...")
        
        # Call Exa API
        response = requests.post(
            "https://api.exa.ai/contents",
            headers={
                "x-api-key": settings.exa_api_key,
                "Content-Type": "application/json"
            },
            json=request_body,
            timeout=30
        )
        
        logger.info(f"Exa API response status: {response.status_code}")
        
        # Check for paywall (402) or other errors
        if response.status_code == 402:
            raise Exception("Exa summary API requires paid plan (402)")
        
        if response.status_code != 200:
            error_text = response.text[:200] if response.text else "No error message"
            raise Exception(f"Exa API error: {response.status_code} - {error_text}")
        
        data = response.json()
        results = data.get("results", [])
        
        logger.info(f"Exa returned {len(results)} results")
        
        if not results:
            raise Exception("No results from Exa API")
        
        # Extract summaries and sources
        summaries = []
        sources = []
        
        for result in results:
            summary_text = result.get('summary')
            if summary_text:
                summaries.append(summary_text)
                logger.info(f"Got summary for: {result.get('url', 'unknown')}")
            
            sources.append(SourceInfo(
                url=result.get('url', ''),
                title=result.get('title'),
                scraped_successfully=bool(summary_text)
            ))
        
        if not summaries:
            raise Exception("No summaries in Exa response")
        
        # Combine summaries
        combined_summary = "\n\n".join(summaries)
        
        logger.info(f"✅ Combined {len(summaries)} summaries from Exa")
        
        return GenerateSummaryResponse(
            summary=combined_summary,
            key_points=[],  # Exa doesn't provide key points
            sources=sources,
            query_context=query,
            generated_by="exa-summary-api"
        )
    
    async def _try_exa_with_text(
        self,
        items: List[str],
        use_ids: bool,
        query: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> GenerateSummaryResponse:
        """
        Try using Exa's text API + Claude for summarization
        
        Fallback if summary API is paywalled
        """
        # Build request body - use ids or urls
        request_body = {
            "text": {"maxCharacters": 5000}
        }
        
        if use_ids:
            request_body["ids"] = items
            logger.info(f"Calling Exa text API with {len(items)} IDs...")
        else:
            request_body["urls"] = items
            logger.info(f"Calling Exa text API with {len(items)} URLs...")
        
        # Call Exa API
        response = requests.post(
            "https://api.exa.ai/contents",
            headers={
                "x-api-key": settings.exa_api_key,
                "Content-Type": "application/json"
            },
            json=request_body,
            timeout=30
        )
        
        logger.info(f"Exa API response status: {response.status_code}")
        
        # Check for paywall or errors
        if response.status_code == 402:
            raise Exception("Exa text API also requires paid plan (402)")
        
        if response.status_code != 200:
            error_text = response.text[:200] if response.text else "No error message"
            raise Exception(f"Exa API error: {response.status_code} - {error_text}")
        
        data = response.json()
        results = data.get("results", [])
        
        logger.info(f"Exa returned {len(results)} results")
        
        if not results:
            raise Exception("No results from Exa API")
        
        # Extract text content
        text_content = []
        sources = []
        
        for result in results:
            text = result.get('text')
            if text and len(text) > 100:
                text_content.append({
                    'url': result.get('url', ''),
                    'title': result.get('title', 'Untitled'),
                    'content': text
                })
                logger.info(f"Got {len(text)} chars from: {result.get('url', 'unknown')}")
            
            sources.append(SourceInfo(
                url=result.get('url', ''),
                title=result.get('title'),
                scraped_successfully=bool(text and len(text) > 100)
            ))
        
        if not text_content:
            raise Exception("No text content from Exa API")
        
        logger.info(f"✅ Got text from {len(text_content)} sources via Exa")
        
        # Use Claude to summarize
        summary, key_points = await self._generate_summary_with_claude(
            text_content,
            query,
            focus_areas
        )
        
        return GenerateSummaryResponse(
            summary=summary,
            key_points=key_points,
            sources=sources,
            query_context=query,
            generated_by="exa-text-api-claude"
        )
    
    async def _try_web_scraping(
        self,
        urls: List[str],
        query: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> GenerateSummaryResponse:
        """
        Fallback: Web scraping + Claude
        
        Used when Exa API is not available or fails
        """
        logger.info(f"Scraping {len(urls[:5])} URLs...")
        
        # Scrape content from URLs
        scraped_content = []
        sources = []
        
        for url in urls[:5]:
            try:
                logger.info(f"Attempting to scrape: {url}")
                content, title = await self._scrape_url(url)
                if content and len(content) > 100:
                    scraped_content.append({
                        'url': url,
                        'title': title or url,
                        'content': content
                    })
                    sources.append(SourceInfo(
                        url=url,
                        title=title,
                        scraped_successfully=True
                    ))
                    logger.info(f"✅ Scraped {len(content)} chars from {url}")
                else:
                    logger.warning(f"⚠️  Insufficient content from {url}")
                    sources.append(SourceInfo(
                        url=url,
                        title=title,
                        scraped_successfully=False
                    ))
            except Exception as e:
                logger.error(f"❌ Error scraping {url}: {e}")
                sources.append(SourceInfo(
                    url=url,
                    title=None,
                    scraped_successfully=False
                ))
        
        # Check if we got any content
        if not scraped_content:
            failed_urls = "\n".join([f"- {s.url}" for s in sources])
            raise Exception(
                f"Could not scrape content from any URLs. "
                f"Try selecting different sources (news sites, blogs work best).\n\n"
                f"Failed URLs:\n{failed_urls}"
            )
        
        # Log success rate
        success_count = len(scraped_content)
        total_count = len(urls[:5])
        logger.info(f"Scraping success: {success_count}/{total_count} URLs")
        
        # Generate summary with Claude
        summary, key_points = await self._generate_summary_with_claude(
            scraped_content,
            query,
            focus_areas
        )
        
        return GenerateSummaryResponse(
            summary=summary,
            key_points=key_points,
            sources=sources,
            query_context=query,
            generated_by="web-scraping-claude"
        )
    
    def _build_summary_query_for_exa(
        self,
        query: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> str:
        """Build query for Exa summary API"""
        parts = ["Create a comprehensive summary"]
        
        if query:
            parts.append(f"about: {query}")
        
        if focus_areas:
            parts.append(f"focusing on: {', '.join(focus_areas)}")
        
        return " ".join(parts)
    
    async def _scrape_url(self, url: str) -> tuple[str, Optional[str]]:
        """
        Scrape content from a URL with multiple fallback strategies
        
        Returns:
            Tuple of (content_text, title)
        """
        try:
            logger.info(f"Scraping: {url}")
            
            # Check if it's a known problematic site
            if 'linkedin.com' in url.lower():
                logger.warning(f"⚠️  LinkedIn detected - these often fail due to bot protection")
            
            # Strategy 1: Try with realistic browser headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            response = requests.get(
                url, 
                timeout=15,
                headers=headers,
                allow_redirects=True,
                verify=True
            )
            
            # Retry with simpler headers if 403/429
            if response.status_code in [403, 429]:
                logger.warning(f"{response.status_code} for {url}, retrying with simpler headers...")
                simple_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=15, headers=simple_headers, allow_redirects=True)
            
            # LinkedIn and some sites return 999 for bot detection
            if response.status_code == 999:
                logger.error(f"LinkedIn bot protection detected (999) for {url}")
                return None, None
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} for {url}")
                return None, None
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get title
            title = None
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            if not title or len(title) < 3:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title.get('content').strip()
            
            # Remove unnecessary elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Try to find main content
            main_content = None
            for selector in ['article', '[role="main"]', 'main', '.article-content', '.post-content', '.entry-content', '.content', '#content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                return None, None
            
            # Extract text
            text = main_content.get_text(separator=' ', strip=True)
            
            # Clean up
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) < 100:
                logger.warning(f"Content too short ({len(text)} chars) for {url}")
                return None, None
            
            text = text[:15000]
            
            logger.info(f"✅ Scraped {len(text)} chars from {url}")
            return text, title
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None, None
    
    async def _generate_summary_with_claude(
        self,
        content_list: List[Dict[str, Any]],
        query: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> tuple[str, List[str]]:
        """
        Generate summary using Claude
        
        Returns:
            Tuple of (summary_text, key_points_list)
        """
        # Build context
        context_parts = []
        for i, content in enumerate(content_list, 1):
            context_parts.append(f"Source {i}: {content['title']}")
            context_parts.append(f"URL: {content['url']}")
            context_parts.append(f"Content: {content['content'][:5000]}")
            context_parts.append("---")
        
        context = "\n\n".join(context_parts)
        
        # Build focus areas string
        focus_str = ""
        if focus_areas:
            focus_str = f"\n\nFocus particularly on: {', '.join(focus_areas)}"
        
        # Build query context
        query_str = ""
        if query:
            query_str = f"\n\nOriginal search query: \"{query}\""
        
        # Create prompt
        prompt = f"""You are an expert research analyst. Create a comprehensive summary from multiple sources.

{query_str}{focus_str}

Information from sources:
{context[:30000]}

Provide:
1. A comprehensive summary (3-4 paragraphs) that synthesizes all sources
2. A list of 5-7 key points

Format as JSON:
{{
  "summary": "Your comprehensive summary...",
  "key_points": ["Point 1", "Point 2", ...]
}}

Write naturally without citations in the text."""

        try:
            logger.info("Calling Claude for summarization...")
            
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON
            import json
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return response_text, []
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            summary = result.get('summary', response_text)
            key_points = result.get('key_points', [])
            
            logger.info("✅ Summary generated with Claude")
            
            return summary, key_points
            
        except Exception as e:
            logger.error(f"Claude summarization failed: {e}")
            # Fallback
            fallback = "\n\n".join([f"{c['title']}: {c['content'][:500]}..." for c in content_list])
            return fallback[:2000], []


# Singleton instance
summary_service = SummaryService()
