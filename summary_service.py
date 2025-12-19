"""
Summary service - handles AI-powered summarization using web scraping + Claude
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from config import settings
import logging
import anthropic
from models import GenerateSummaryResponse, SourceInfo

logger = logging.getLogger(__name__)


class SummaryService:
    """Service class for AI-powered summarization"""
    
    def __init__(self):
        """Initialize Claude client if API key is available"""
        self.anthropic_client = None
        if settings.anthropic_api_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    async def generate_summary(
        self,
        urls: List[str],
        query: Optional[str] = None,
        focus_areas: Optional[List[str]] = None
    ) -> GenerateSummaryResponse:
        """
        Generate AI summary from URLs using web scraping + Claude
        
        Args:
            urls: List of URLs to summarize
            query: Original search query for context
            focus_areas: What to focus on in the summary
            
        Returns:
            GenerateSummaryResponse with AI summary and sources
        """
        if not self.anthropic_client:
            raise Exception("Anthropic API key not configured. Please set ANTHROPIC_API_KEY in .env")
        
        logger.info(f"Generating summary for {len(urls)} URLs")
        
        # Step 1: Scrape content from URLs
        scraped_content = []
        sources = []
        
        for url in urls[:5]:  # Limit to 5 URLs
            try:
                content, title = await self._scrape_url(url)
                if content:
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
                    sources.append(SourceInfo(
                        url=url,
                        title=None,
                        scraped_successfully=False
                    ))
                    logger.warning(f"⚠️  Failed to scrape {url}")
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                sources.append(SourceInfo(
                    url=url,
                    title=None,
                    scraped_successfully=False
                ))
        
        if not scraped_content:
            raise Exception("Could not scrape any content from the provided URLs")
        
        # Step 2: Generate summary with Claude
        summary, key_points = await self._generate_summary_with_claude(
            scraped_content,
            query,
            focus_areas
        )
        
        return GenerateSummaryResponse(
            summary=summary,
            key_points=key_points,
            sources=sources,
            query_context=query
        )
    
    async def _scrape_url(self, url: str) -> tuple[str, Optional[str]]:
        """
        Scrape content from a URL
        
        Returns:
            Tuple of (content_text, title)
        """
        try:
            logger.info(f"Scraping: {url}")
            
            # Fetch the page
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
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
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            text = text[:10000]  # First 10k characters
            
            return text, title
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None, None
    
    async def _generate_summary_with_claude(
        self,
        scraped_content: List[Dict[str, Any]],
        query: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> tuple[str, List[str]]:
        """
        Generate summary using Claude
        
        Returns:
            Tuple of (summary_text, key_points_list)
        """
        # Build context from scraped content
        context_parts = []
        for i, content in enumerate(scraped_content, 1):
            context_parts.append(f"Source {i}: {content['title']}")
            context_parts.append(f"URL: {content['url']}")
            context_parts.append(f"Content: {content['content'][:5000]}")  # First 5k chars per source
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
        
        # Create prompt for Claude
        prompt = f"""You are an expert research analyst. I have gathered information from multiple web sources and need you to create a comprehensive, well-structured summary.

{query_str}{focus_str}

Information from sources:
{context[:30000]}

Please provide:

1. A comprehensive summary (3-4 paragraphs) that:
   - Synthesizes information from all sources
   - Identifies common themes and key findings
   - Highlights important insights and takeaways
   - Is written in clear, professional language

2. A list of 5-7 key points extracted from the sources

Format your response as JSON:
{{
  "summary": "Your comprehensive summary here...",
  "key_points": ["Point 1", "Point 2", "Point 3", ...]
}}

Important:
- Do NOT include citations or source numbers in the summary text
- Write in a natural, flowing style
- Focus on the most important and relevant information
- If sources conflict, acknowledge different perspectives"""

        try:
            logger.info("Calling Claude for summarization...")
            
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            logger.info("Received response from Claude")
            
            # Extract JSON
            import json
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # Fallback if no JSON found
                return response_text, []
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            summary = result.get('summary', response_text)
            key_points = result.get('key_points', [])
            
            logger.info("✅ Summary generated successfully")
            
            return summary, key_points
            
        except Exception as e:
            logger.error(f"Failed to generate summary with Claude: {e}")
            # Return a basic concatenation as fallback
            fallback_summary = "\n\n".join([
                f"From {c['title']}: {c['content'][:500]}..."
                for c in scraped_content
            ])
            return fallback_summary[:2000], []


# Singleton instance
summary_service = SummaryService()
