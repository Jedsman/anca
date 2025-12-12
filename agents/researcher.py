import logging
from typing import List, Set
from app.state import ArticleState
from tools.search_tool import _duckduckgo_search
from tools.scraper_tool import ScraperTool
from tools.rag_tool import RAGTool
import re

logger = logging.getLogger(__name__)

# Compile regex for URL extraction
URL_PATTERN = re.compile(r'URL: (https?://[^\s]+)')

def researcher_node(state: ArticleState):
    """
    Researcher Node:
    1. Collects all search queries from the Blueprint.
    2. Searches for URLs using DuckDuckGo.
    3. Scrapes and Ingests content into ChromaDB.
    """
    logger.info("[RESEARCHER] Starting research phase...")
    queries = set()
    
    # 1. Collect unique queries
    for section in state["blueprint"].sections:
        if section.search_queries:
            for q in section.search_queries:
                queries.add(q)
    
    logger.info(f"[RESEARCHER] Found {len(queries)} unique queries to research.")
    
    # Initialize Tools
    scraper = ScraperTool()
    rag = RAGTool()
    
    # Track processed URLs to avoid duplicates
    processed_urls: Set[str] = set()
    
    # Limit total sources to avoid excessive processing time
    MAX_SOURCES = 8
    
    # 2. Search & Ingest Loop
    for query in queries:
        if len(processed_urls) >= MAX_SOURCES:
            logger.info(f"[RESEARCHER] detailed source limit reached ({MAX_SOURCES}). Stopping research.")
            break

        logger.info(f"[RESEARCHER] Searching for: {query}")
        
        # Search (using the internal DDGS wrapper directly or the formatted one)
        search_results_text = _duckduckgo_search(query, num_results=2)
        
        if not search_results_text or "No search results" in search_results_text:
             logger.warning(f"[RESEARCHER] No results for: {query}")
             continue
             
        # Extract URLs
        urls = URL_PATTERN.findall(search_results_text)
        
        for url in urls:
            if len(processed_urls) >= MAX_SOURCES:
                break
                
            if url in processed_urls:
                continue
                
            logger.info(f"[RESEARCHER] Processing URL: {url}")
            try:
                # A. Scrape (Writes to .cache/scraper)
                scraper._run(url=url)
                
                # B. Ingest (Reads from .cache/scraper -> Writes to Chroma)
                rag.ingest(url=url)
                
                processed_urls.add(url)
                
            except Exception as e:
                logger.error(f"[RESEARCHER] Error processing {url}: {e}")
                
    logger.info(f"[RESEARCHER] Research complete. Ingested {len(processed_urls)} new sources.")
    return state # Pass state through unchanged
