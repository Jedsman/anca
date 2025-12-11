import logging
import requests
import urllib.parse
from typing import List, Dict
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ddgs import DDGS

logger = logging.getLogger(__name__)

# --- Google URL Search (Primary Strategy) ---

def _google_url_search(query: str, num_results: int = 5) -> str:
    """
    Search Google by constructing search URLs and parsing HTML results.

    This gives us REAL Google rankings without needing an API key.
    Google may block this, so we use it as primary but have DDG fallback.
    """
    try:
        # Encode query for URL
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"

        # Headers to appear as a regular browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Make request
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML to extract results
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []

        # Try multiple strategies to find search results
        # Strategy 1: Standard div.g containers (most common)
        search_results = soup.find_all('div', class_='g')

        # Strategy 2: If no results, try alternative container classes
        if not search_results:
            search_results = soup.find_all('div', {'data-sokoban-container': True})

        # Strategy 3: Try finding all <a> tags with /url?q= pattern (Google result links)
        if not search_results:
            all_links = soup.find_all('a', href=True)
            search_results = [link.parent.parent for link in all_links if '/url?q=' in link.get('href', '')]

        for idx, result in enumerate(search_results[:num_results], 1):
            try:
                # Extract title (try multiple methods)
                title_elem = result.find('h3')
                if not title_elem:
                    title_elem = result.find('h2')
                title = title_elem.text if title_elem else "No title"

                # Extract URL (handle different formats)
                link_elem = result.find('a', href=True)
                url = ''
                if link_elem:
                    href = link_elem.get('href', '')
                    # Clean up Google redirect URLs
                    if '/url?q=' in href:
                        url = href.split('/url?q=')[1].split('&')[0]
                    else:
                        url = href

                # Skip non-http URLs (like javascript:, #, etc)
                if not url.startswith('http'):
                    continue

                # Extract snippet (try multiple selectors)
                snippet_elem = result.find('div', class_=['VwiC3b', 'yXK7lf', 'IsZvec'])
                if not snippet_elem:
                    # Try finding any div with text content
                    snippet_elem = result.find('div', class_=lambda x: x and 'style' not in x)
                snippet = snippet_elem.text if snippet_elem else "No description available"

                if url:
                    results.append(f"{idx}. **{title}**\n   URL: {url}\n   {snippet[:150]}...\n")
            except Exception as e:
                # Skip this result if parsing fails
                logger.debug(f"Failed to parse result {idx}: {e}")
                continue

        if results:
            logger.info(f"✅ Google search successful: found {len(results)} results")
            return "\n".join(results)
        else:
            # Parsing failed, likely HTML structure changed
            logger.warning("⚠️ Google search returned results but parsing failed")
            return None

    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Google search failed (network error): {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Google search failed (parsing error): {e}")
        return None

# --- DuckDuckGo Search (Fallback Strategy) ---

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _execute_ddgs_search(query: str, max_results: int = 7) -> List[Dict]:
    """Execute DDGS search with retry logic."""
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))

def _duckduckgo_search(query: str, num_results: int = 4) -> str:
    """
    Search using DuckDuckGo via DDGS library.
    Returns structured results with URLs for the researcher to scrape.
    """
    try:
        logger.info(f"Searching DuckDuckGo for: {query}")

        # Use DDGS directly for structured results with URLs
        raw_results = _execute_ddgs_search(query, max_results=num_results)

        if not raw_results:
            logger.warning("DuckDuckGo returned no results")
            return "No search results found."

        # Format results with URLs prominently displayed
        formatted_results = []
        for idx, r in enumerate(raw_results, 1):
            title = r.get('title', 'No title')
            url = r.get('href', r.get('link', 'No URL'))
            snippet = r.get('body', r.get('snippet', 'No description'))[:200]

            formatted_results.append(
                f"{idx}. **{title}**\n"
                f"   URL: {url}\n"
                f"   {snippet}...\n"
            )

        logger.info(f"DuckDuckGo search successful: found {len(formatted_results)} results")
        return "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return f"Error: Search failed. {str(e)}"

# --- Hybrid Search Tool ---

@tool
def web_search(query: str) -> str:
    """
    Search the web for results with URLs.

    Uses DuckDuckGo as the primary search engine (reliable, returns URLs).
    Google scraping is disabled due to bot detection.

    Args:
        query: The search query (e.g., "comprehensive guide to coffee brewing")

    Returns:
        A string containing search results with titles, snippets, and URLs.
    """
    logger.info(f"Searching for: {query}")

    # Use DuckDuckGo directly (Google scraping is blocked)
    return _duckduckgo_search(query)
