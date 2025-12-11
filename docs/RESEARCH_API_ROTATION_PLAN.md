# Research API Rotation Strategy

## Current Implementation ✅
- **Primary**: Google URL Search (scraping HTML, no API key needed)
- **Fallback**: DuckDuckGo Search (via `langchain-community`)
- **Status**: Hybrid system implemented - tries Google first, falls back to DDG
- **Advantages**:
  - Real Google rankings (best for SEO research)
  - Automatic fallback when Google blocks/rate-limits
  - No API keys required
- **Limitations**:
  - Google may block aggressive scraping
  - HTML parsing can break if Google changes structure
  - No SEO metrics (keyword difficulty, search volume)

## Future Enhancement: Free Tier API Rotation

### Goal
Rotate between multiple free-tier search APIs to:
1. Avoid rate limits by distributing requests
2. Increase reliability with fallback options
3. Get diverse search results from multiple sources
4. Maximize free tier usage before needing paid plans

---

## Recommended Free Tier APIs

### 1. **Brave Search API** ⭐ (Recommended Primary)
- **Free Tier**: 2,000 queries/month
- **Pros**: Privacy-focused, good quality results, reliable API
- **Cons**: Requires API key (free)
- **Setup**: https://brave.com/search/api/
```python
# pip install langchain-community
from langchain_community.utilities import BraveSearchWrapper
```

### 2. **SearchAPI.io**
- **Free Tier**: 100 searches/month (limited but useful)
- **Pros**: Google SERP data, clean API
- **Cons**: Small free tier
- **Setup**: https://www.searchapi.io/

### 3. **SerpAPI** (Google Search)
- **Free Tier**: 100 searches/month
- **Pros**: Real Google results, best quality, SEO metrics available
- **Cons**: Small free tier, paid after 100
- **Use Case**: Reserve for competitive keyword research
- **Setup**: https://serpapi.com/

### 4. **Tavily AI** ⭐ (AI-Optimized)
- **Free Tier**: 1,000 requests/month
- **Pros**: Purpose-built for AI agents, excellent content extraction
- **Cons**: Newer service
- **Setup**: https://tavily.com/
```python
# pip install tavily-python
from tavily import TavilyClient
```

### 5. **DuckDuckGo** (Current - No API Key)
- **Free Tier**: Unlimited (with rate limits)
- **Pros**: No API key needed, works locally
- **Cons**: Rate limiting, less reliable
- **Use Case**: Fallback when others are exhausted

---

## Implementation Strategy

### Phase 1: Add API Keys (Environment Variables)
```env
# .env.example
BRAVE_API_KEY=your_brave_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
SERPAPI_KEY=your_serpapi_key_here
SEARCHAPI_KEY=your_searchapi_key_here
```

### Phase 2: Create Rotation Logic
```python
# tools/search_tool.py (future implementation)

class SearchAPIRotator:
    """Rotate between multiple search APIs to maximize free tiers."""

    def __init__(self):
        self.apis = [
            {'name': 'brave', 'limit': 2000, 'used': 0, 'priority': 1},
            {'name': 'tavily', 'limit': 1000, 'used': 0, 'priority': 2},
            {'name': 'ddg', 'limit': float('inf'), 'used': 0, 'priority': 3},
            {'name': 'serpapi', 'limit': 100, 'used': 0, 'priority': 4},  # Reserve for important queries
        ]

    def get_next_api(self):
        """Select next available API based on usage and priority."""
        available = [api for api in self.apis if api['used'] < api['limit']]
        if not available:
            # All exhausted, reset to DDG (unlimited but rate limited)
            return 'ddg'
        return min(available, key=lambda x: x['priority'])['name']

    def search(self, query: str):
        """Execute search with automatic API rotation."""
        api = self.get_next_api()

        if api == 'brave':
            return self._brave_search(query)
        elif api == 'tavily':
            return self._tavily_search(query)
        elif api == 'serpapi':
            return self._serpapi_search(query)
        else:  # ddg fallback
            return self._ddg_search(query)
```

### Phase 3: Tracking Usage
```python
# Store monthly usage in a simple JSON file or database
# Reset on the 1st of each month
# Log which API was used for each search
```

---

## Monthly Free Tier Budget

With all free tiers combined:
- Brave: 2,000 queries
- Tavily: 1,000 queries
- SearchAPI: 100 queries
- SerpAPI: 100 queries
- DuckDuckGo: Unlimited (rate limited)

**Total: ~3,200+ queries/month** before hitting any paid limits.

At 4 queries per article (varied search strategy), that's **800 articles/month** on free tiers.

---

## Priority Order (Recommended)

1. **Brave** - Use first (best free tier: 2,000/month)
2. **Tavily** - Use for AI-optimized content extraction
3. **DuckDuckGo** - Fallback (unlimited but rate limited)
4. **SerpAPI** - Reserve for competitive keyword research only

---

## Implementation Checklist

- [ ] Sign up for Brave Search API (free tier)
- [ ] Sign up for Tavily AI (free tier)
- [ ] Add API keys to `.env` and `.env.example`
- [ ] Implement `SearchAPIRotator` class in `tools/search_tool.py`
- [ ] Add usage tracking (JSON file or SQLite)
- [ ] Update `agents/researcher.py` to use rotator
- [ ] Add logging to track which API is used per search
- [ ] Set up monthly usage reset cron job

---

## Cost Estimate (If Scaling Beyond Free)

If you exceed free tiers and need to go paid:

| Service | Cost | Use Case |
|---------|------|----------|
| Brave Search | $5/month (unlimited) | Primary search |
| Tavily AI | $50/month (5,000 queries) | AI content extraction |
| SerpAPI | $50/month (5,000 searches) | Google SERP data |

**Recommendation**: Stay on free tiers initially, only upgrade if you're generating 800+ articles/month.

---

## Testing Plan

1. Keep DuckDuckGo as current implementation
2. Add Brave as first alternative (easy signup, generous free tier)
3. Test rotation logic with small traffic
4. Monitor quality differences between APIs
5. Scale to other APIs as needed

---

**Status**: Documented for future implementation
**Priority**: Medium (implement after core workflow is proven)
**Dependencies**: Working article generation pipeline, proven SEO results
