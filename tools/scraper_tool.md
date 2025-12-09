# ScraperTool

**Stage:** 1  
**Type:** Web scraping with ethical controls

## Purpose
Scrapes websites and returns LLM-ready content chunks with metadata.

## Features
- **Robots.txt compliance** - Respects site rules
- **Crawl-delay support** - Honors rate limits
- **Configurable caching** - 7-day default (prevents re-scraping)
- **Metadata preservation** - URL, timestamp, title
- **Smart chunking** - Tiktoken-based splitting (1000 tokens, 200 overlap)

## Configuration
```python
scraper = ScraperTool()
scraper.chunk_size = 1000
scraper.chunk_overlap = 200
scraper.cache_enabled = True
scraper.cache_ttl_days = 7  # 7-30 days recommended
```

## Usage
```python
from tools import ScraperTool

scraper = ScraperTool()
result = scraper._run("https://example.com")
# Returns formatted string with chunks
```

## Output Format
```
# Scraped Content from: URL
Title: Page Title
Scraped at: 2025-12-08T14:00:00
Total chunks: 3

## Chunk 1/3
[content...]
```
