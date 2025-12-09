from crewai.tools import BaseTool
from typing import Any, List, Dict, Optional
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from robotexclusionrulesparser import RobotExclusionRulesParser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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


class ScraperTool(BaseTool):
    name: str = "ScraperTool"
    description: str = "Scrapes a website and returns its content as LLM-ready chunks with metadata."

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
    def _load_and_transform(self, url: str) -> List[Dict[str, Any]]:
        """Load and transform web content into LLM-ready chunks with metadata."""
        
        # Check cache first
        cached_content = self._get_cached_content(url)
        if cached_content:
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
            docs_transformed = bs_transformer.transform_documents(
                docs,
                tags_to_extract=[
                    "article", "main", "section",  # Semantic content containers
                    "h1", "h2", "h3", "h4", "h5", "h6",  # Headings
                    "p", "li", "blockquote",  # Text content
                    "pre", "code",  # Code blocks
                    "table", "th", "td",  # Tables
                    "a"  # Links (for context)
                ],
                tags_to_remove=["script", "style", "nav", "footer", "aside", "iframe"]
            )

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
            
            # Save to cache
            self._save_to_cache(url, chunks)
            
            return chunks

        except Exception as e:
            logger.error(f"Error during scraping {url}: {type(e).__name__}: {e}")
            raise

    def _run(self, url: str) -> str:
        """
        Main entry point for the scraper tool.
        
        Args:
            url: The URL to scrape
            
        Returns:
            A formatted string containing the scraped content with metadata
        """
        try:
            logger.info(f"Starting scrape for {url}")
            chunks = self._load_and_transform(url)
            
            if not chunks:
                return f"Failed to scrape content from {url}"
            
            # Format the output for better agent consumption
            metadata = chunks[0]['metadata']
            output_parts = [
                f"# Scraped Content from: {url}",
                f"Title: {metadata.get('source_title', 'Unknown')}",
                f"Scraped at: {metadata.get('scraped_at', 'Unknown')}",
                f"Total chunks: {len(chunks)}",
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