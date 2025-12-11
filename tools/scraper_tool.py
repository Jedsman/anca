from crewai.tools import BaseTool
from typing import Any, List, Dict, Optional, Type
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from robotexclusionrulesparser import RobotExclusionRulesParser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, Field, field_validator
import time
import random
from urllib.parse import urlparse
import requests
import logging
from datetime import datetime
import hashlib
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperToolSchema(BaseModel):
    """Input schema for ScraperTool."""
    url: str = Field(..., description="The URL to scrape.")
    keywords: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of keywords to filter chunks. Only chunks containing at least one keyword are kept."
    )
    
    @field_validator('keywords', mode='before')
    @classmethod
    def sanitize_keywords(cls, v):
        """Handle string 'None' or other invalid values for keywords."""
        if v is None:
            return None
        if isinstance(v, str):
            if v.lower() in ('none', 'null', ''):
                return None
            # Single keyword as string - convert to list
            return [v]
        if isinstance(v, list):
            # Filter out None and 'None' strings from list
            cleaned = [k for k in v if k and str(k).lower() not in ('none', 'null', '')]
            return cleaned if cleaned else None
        return v


class ScraperTool(BaseTool):
    name: str = "ScraperTool"
    description: str = (
        "Scrapes a website URL and returns its content as text chunks. "
        "Provide the URL to scrape. Optionally provide keywords to filter relevant content."
    )
    args_schema: Type[BaseModel] = ScraperToolSchema

    # Configuration
    user_agent: str = "ANCA-Bot/1.0 (Educational Research; +https://github.com/yourproject/anca)"
    chunk_size: int = 1000
    chunk_overlap: int = 200  # Overlap to preserve context between chunks
    min_delay: float = 5.0
    max_delay: float = 15.0
    cache_enabled: bool = True
    cache_dir: str = ".cache/scraper"
    cache_ttl_days: int = 7  # Cache duration in days (7-30 recommended)
    
    # Internal caches
    _robots_parsers: dict = {}  # Cache for robots.txt parsers
    _crawl_delays: dict = {}  # Cache for crawl-delay directives
    _content_cache: dict = {}  # In-memory cache for scraped content

    def __init__(self, **data):
        super().__init__(**data)
        if self.cache_enabled:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached_content(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached content if available and not expired."""
        if not self.cache_enabled:
            return None
            
        cache_key = self._get_cache_key(url)
        cache_file = Path(self.cache_dir) / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    # Check if cache is within TTL
                    cache_time = datetime.fromisoformat(cached_data['timestamp'])
                    cache_age_days = (datetime.now() - cache_time).total_seconds() / 86400
                    if cache_age_days < self.cache_ttl_days:
                        logger.info(f"Using cached content for {url} (age: {cache_age_days:.1f} days)")
                        return cached_data['chunks']
                    else:
                        logger.info(f"Cache expired for {url} (age: {cache_age_days:.1f} days, TTL: {self.cache_ttl_days} days)")
            except Exception as e:
                logger.warning(f"Error reading cache for {url}: {e}")
        
        return None

    def _save_to_cache(self, url: str, chunks: List[Dict[str, Any]]):
        """Save scraped content to cache."""
        if not self.cache_enabled:
            return
            
        cache_key = self._get_cache_key(url)
        cache_file = Path(self.cache_dir) / f"{cache_key}.json"
        
        try:
            cache_data = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'chunks': chunks
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Cached content for {url}")
        except Exception as e:
            logger.warning(f"Error saving cache for {url}: {e}")

    def _parse_robots_txt(self, url: str) -> Optional[RobotExclusionRulesParser]:
        """Parse robots.txt and extract crawl-delay if present."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        if domain not in self._robots_parsers:
            robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
            try:
                headers = {'User-Agent': self.user_agent}
                response = requests.get(robots_url, timeout=5, headers=headers)
                
                if response.status_code == 200:
                    parser = RobotExclusionRulesParser()
                    parser.parse(response.text)
                    self._robots_parsers[domain] = parser
                    
                    # Extract crawl-delay if present
                    for line in response.text.split('\n'):
                        if line.lower().startswith('crawl-delay:'):
                            try:
                                delay = float(line.split(':')[1].strip())
                                self._crawl_delays[domain] = delay
                                logger.info(f"Found Crawl-delay: {delay}s for {domain}")
                            except ValueError:
                                pass
                    
                    logger.info(f"Successfully parsed robots.txt for {domain}")
                else:
                    logger.info(f"No robots.txt found for {domain} (status: {response.status_code})")
                    self._robots_parsers[domain] = None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error fetching robots.txt for {domain}: {e}")
                self._robots_parsers[domain] = None

        return self._robots_parsers.get(domain)

    def _is_url_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        parser = self._parse_robots_txt(url)
        
        if parser:
            allowed = parser.is_allowed(self.user_agent, url)
            if not allowed:
                logger.warning(f"URL blocked by robots.txt: {url}")
            return allowed
        
        return True  # If no parser or robots.txt not found, assume allowed

    def _get_delay_for_domain(self, url: str) -> float:
        """Get appropriate delay for domain, respecting crawl-delay directive."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Check if we have a crawl-delay directive
        if domain in self._crawl_delays:
            crawl_delay = self._crawl_delays[domain]
            # Use crawl-delay but add some randomness
            return crawl_delay + random.uniform(0, 2)
        
        # Use default random delay
        return random.uniform(self.min_delay, self.max_delay)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError))
    )
    def _load_and_transform(self, url: str, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Load and transform web content into LLM-ready chunks with metadata."""
        
        # Check cache first (Not using keywords in cache key yet, simple URL cache)
        # Improvement: If we use keywords, we should maybe re-filter cached content?
        # For now, let's load cached content and apply filter if needed.
        cached_content = self._get_cached_content(url)
        if cached_content:
            logger.info(f"Loaded {len(cached_content)} chunks from cache for {url}")
            # Apply keyword filter to cached content if provided
            if keywords:
                filtered = []
                for chunk in cached_content:
                    text_lower = chunk['content'].lower()
                    if any(k.lower() in text_lower for k in keywords):
                        filtered.append(chunk)
                logger.info(f"Filtered cached content: {len(filtered)}/{len(cached_content)} chunks matched keywords {keywords}")
                return filtered
            return cached_content
        
        # Check robots.txt
        if not self._is_url_allowed(url):
            logger.warning(f"Skipping {url} due to robots.txt exclusion")
            return []

        # Respect crawl-delay
        delay = self._get_delay_for_domain(url)
        logger.info(f"Waiting {delay:.2f}s before scraping {url}")
        time.sleep(delay)

        try:
            # Step 1: Load the web page using a headless browser (Chromium)
            logger.info(f"Loading {url} with headless browser")
            loader = AsyncChromiumLoader(
                [url],
                user_agent=self.user_agent
            )
            docs = loader.load()

            if not docs:
                logger.error(f"No documents loaded from {url}")
                return []

            # Step 2: Transform and clean the HTML content
            logger.info(f"Transforming HTML content from {url}")
            bs_transformer = BeautifulSoupTransformer()

            # Extract main content tags and remove noise
            # NOTE: Including "div" is CRITICAL - most modern websites use div containers for content
            docs_transformed = bs_transformer.transform_documents(
                docs,
                tags_to_extract=[
                    # Semantic containers
                    "article", "main", "section", "div",  # div is critical for modern sites
                    # Headings
                    "h1", "h2", "h3", "h4", "h5", "h6",
                    # Content
                    "p", "li", "ul", "ol", "blockquote",
                    "span", "strong", "em", "b", "i",  # Inline text elements
                    # Data
                    "table", "th", "td", "tr", "tbody", "thead",
                    # Links
                    "a"
                ],
                tags_to_remove=[
                    # Scripts & styles
                    "script", "style", "noscript",
                    # Navigation
                    "nav", "header", "footer", "aside",
                    # Forms & interactive
                    "form", "button", "input", "select", "textarea",
                    # Media & visual
                    "iframe", "svg", "canvas", "figure", "figcaption", "img", "video", "audio",
                    # Ads & tracking
                    "ins", "ad"
                ]
            )

            # Log extracted content length for debugging
            if docs_transformed:
                extracted_text = docs_transformed[0].page_content if docs_transformed else ""
                logger.info(f"Extracted {len(extracted_text)} characters from {url}")
                if len(extracted_text) == 0:
                    logger.warning(f"⚠️ Zero content extracted from {url} - possible parsing issue")
            else:
                logger.warning(f"⚠️ No documents after transformation for {url}")

            # Extract metadata from the first document
            metadata = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'source_title': docs[0].metadata.get('title', 'Unknown'),
            }

            # Step 3: Split the clean text into smaller chunks for the LLM's context window
            logger.info(f"Splitting content into chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            splits = splitter.split_documents(docs_transformed)
            logger.info(f"Created {len(splits)} splits from extracted content")

            # Fallback: If tag-based extraction produced nothing, try more permissive extraction
            if not splits or len(splits) == 0:
                logger.warning(f"Tag-based extraction failed for {url}, trying fallback method")

                # Fallback: Extract all text, only remove noise tags
                docs_fallback = bs_transformer.transform_documents(
                    docs,
                    tags_to_extract=None,  # Extract everything
                    tags_to_remove=["script", "style", "noscript", "nav", "header", "footer",
                                    "aside", "form", "button", "input", "select", "textarea",
                                    "iframe", "svg", "canvas", "img", "video", "audio"]
                )

                if docs_fallback:
                    splits = splitter.split_documents(docs_fallback)
                    logger.info(f"Fallback extraction created {len(splits)} splits")

            # Create chunks with metadata
            chunks = []
            for i, split in enumerate(splits):
                chunk_data = {
                    'content': split.page_content,
                    'metadata': {
                        **metadata,
                        'chunk_index': i,
                        'total_chunks': len(splits)
                    }
                }
                chunks.append(chunk_data)
            
            logger.info(f"Successfully scraped {url}: {len(chunks)} chunks created")
            
            # Save raw chunks to cache (before filtering, so we have full content)
            self._save_to_cache(url, chunks)
            
            # Apply keyword filter if provided
            if keywords:
                filtered_chunks = []
                for chunk in chunks:
                    text_lower = chunk['content'].lower()
                    if any(k.lower() in text_lower for k in keywords):
                        filtered_chunks.append(chunk)
                logger.info(f"Filtered content: {len(filtered_chunks)}/{len(chunks)} chunks matched keywords {keywords}")
                return filtered_chunks
            
            return chunks

        except Exception as e:
            logger.error(f"Error during scraping {url}: {type(e).__name__}: {e}")
            raise

    def _run(self, url: str, keywords: Optional[List[str]] = None) -> str:
        """
        Main entry point for the scraper tool.
        
        Args:
            url: The URL to scrape
            keywords: Optional list of keywords. Only chunks containing at least one keyword are kept.
            
        Returns:
            A formatted string containing the scraped content with metadata
        """
        try:
            # Sanitize keywords: handle string "None" or empty values
            if keywords is not None:
                if isinstance(keywords, str):
                    if keywords.lower() in ('none', 'null', ''):
                        keywords = None
                    else:
                        # Single keyword passed as string, convert to list
                        keywords = [keywords]
                elif isinstance(keywords, list):
                    # Filter out None, 'None', and empty strings from list
                    keywords = [k for k in keywords if k and str(k).lower() not in ('none', 'null', '')]
                    if not keywords:
                        keywords = None
            
            logger.info(f"Starting scrape for {url} (keywords={keywords})")
            chunks = self._load_and_transform(url, keywords)
            
            if not chunks:
                if keywords:
                    return f"Failed to scrape relevant content from {url}. Content found but no chunks matched keywords: {keywords}"
                return f"Failed to scrape content from {url}"
            
            # Format the output for better agent consumption
            metadata = chunks[0]['metadata']
            output_parts = [
                f"# Scraped Content from: {url}",
                f"Title: {metadata.get('source_title', 'Unknown')}",
                f"Scraped at: {metadata.get('scraped_at', 'Unknown')}",
                f"Total relevant chunks: {len(chunks)}",
                "",
                "---",
                ""
            ]
            
            # Add all chunk content
            for i, chunk in enumerate(chunks):
                output_parts.append(f"## Chunk {i + 1}/{len(chunks)}")
                output_parts.append(chunk['content'])
                output_parts.append("")
            
            return "\n".join(output_parts)
            
        except Exception as e:
            logger.error(f"Failed to scrape {url} after all retries: {type(e).__name__}: {e}")
            return f"Error scraping {url}: {str(e)}"