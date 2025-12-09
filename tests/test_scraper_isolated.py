"""
Isolated test for ScraperTool
Tests web scraping functionality without agents
"""
from tools.scraper_tool import ScraperTool
import time

def test_scraper():
    print("=" * 60)
    print("Testing ScraperTool in isolation")
    print("=" * 60)
    
    scraper = ScraperTool()
    
    # Test with a fast, reliable site
    test_url = "https://example.com"
    
    print(f"\n📡 Scraping: {test_url}")
    start_time = time.time()
    
    result = scraper._run(test_url)
    
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Time: {elapsed:.2f}s")
    print(f"📄 Result length: {len(result)} chars")
    print(f"\n📝 Preview (first 500 chars):")
    print("-" * 60)
    print(result[:500])
    print("-" * 60)
    
    # Test cache
    print(f"\n🔄 Testing cache (should be instant)...")
    start_time = time.time()
    cached_result = scraper._run(test_url)
    cache_elapsed = time.time() - start_time
    
    print(f"⏱️  Cache time: {cache_elapsed:.2f}s")
    print(f"✅ Cache working: {cache_elapsed < 1.0}")
    
    return result

if __name__ == "__main__":
    test_scraper()
