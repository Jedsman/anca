# Market Researcher Agent

**Model:** `llama3.1:8b` (fast, focused)  
**Temperature:** 0.5 (consistent results)

## Purpose
Identifies low-competition, high-intent long-tail keywords for content creation.

## Capabilities
- SEO keyword analysis
- Competition assessment
- Topic niche identification
- Source article discovery

## Tools
- ScraperTool (web research)

## Output
- Chosen long-tail keyword
- High-ranking source article URL

## Usage
```python
from agents import create_researcher
from tools.scraper_tool import ScraperTool

researcher = create_researcher(tools=[ScraperTool()])
```
